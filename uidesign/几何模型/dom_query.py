#!/usr/bin/env python3
"""
直接查询布局引擎拿 UI 结构 —— 不用像素扫描
用法: python3 dom_query.py <html文件> [宽度] [高度] [像素密度]
"""
import json, subprocess, time, urllib.request, sys, os, signal

W = int(sys.argv[2]) if len(sys.argv) > 2 else 390
H = int(sys.argv[3]) if len(sys.argv) > 3 else 780
DENS = float(sys.argv[4]) if len(sys.argv) > 4 else 3.0
PORT = 9333

JS = r"""
(function(){
  var out = [];
  var els = document.querySelectorAll('*');
  for (var i = 0; i < els.length; i++) {
    var e = els[i];
    var r = e.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    var cs = getComputedStyle(e);
    var tag = e.tagName.toLowerCase();
    var isInput = (tag === 'input' || tag === 'button' || tag === 'select' ||
                   tag === 'textarea' || tag === 'a' ||
                   e.getAttribute('onclick') !== null ||
                   cs.cursor === 'pointer');
    var txt = '';
    if (e.children.length === 0) txt = (e.textContent || '').trim();
    else {
      for (var c = 0; c < e.childNodes.length; c++) {
        if (e.childNodes[c].nodeType === 3) txt += e.childNodes[c].nodeValue;
      }
      txt = txt.trim();
    }
    out.push({
      tag: tag,
      id: e.id || '',
      cls: (typeof e.className === 'string') ? e.className : '',
      text: txt.slice(0, 40),
      x: Math.round(r.x * 10) / 10,
      y: Math.round(r.y * 10) / 10,
      w: Math.round(r.width * 10) / 10,
      h: Math.round(r.height * 10) / 10,
      bg: cs.backgroundColor,
      color: cs.color,
      fs: cs.fontSize,
      radius: cs.borderRadius,
      interactive: isInput
    });
  }
  return JSON.stringify(out);
})()
"""

def main():
    html = os.path.abspath(sys.argv[1])
    proc = subprocess.Popen([
        'google-chrome', '--headless=new', '--disable-gpu',
        '--no-sandbox', '--disable-dev-shm-usage',
        f'--remote-debugging-port={PORT}',
        f'--window-size={W},{H}',
        '--hide-scrollbars', '--force-device-scale-factor=1',
        '--remote-allow-origins=*',
        'about:blank'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    ws_url = None
    for _ in range(60):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json', timeout=2) as r:
                tabs = json.load(r)
            for t in tabs:
                if t.get('type') == 'page':
                    ws_url = t['webSocketDebuggerUrl']
                    break
            if ws_url:
                break
        except Exception:
            pass
    if not ws_url:
        print("❌ 无法连接 Chrome DevTools")
        proc.kill()
        return 1

    try:
        import websocket
    except ImportError:
        print("❌ 缺 websocket-client")
        proc.kill()
        return 1

    ws = websocket.create_connection(ws_url, timeout=30)
    mid = [0]

    def send(method, params=None):
        mid[0] += 1
        ws.send(json.dumps({'id': mid[0], 'method': method, 'params': params or {}}))
        while True:
            msg = json.loads(ws.recv())
            if msg.get('id') == mid[0]:
                return msg

    send('Page.enable')
    send('Runtime.enable')
    send('Emulation.setDeviceMetricsOverride', {
        'width': W, 'height': H, 'deviceScaleFactor': 1, 'mobile': True})
    send('Page.navigate', {'url': 'file://' + html})
    time.sleep(2.5)

    res = send('Runtime.evaluate', {'expression': JS, 'returnByValue': True})
    data = json.loads(res['result']['result']['value'])
    ws.close()
    proc.send_signal(signal.SIGTERM)
    time.sleep(0.5)
    try:
        proc.kill()
    except Exception:
        pass

    print(f"=== 布局引擎直查: {os.path.basename(html)}  {W}x{H} ===")
    print(f"共 {len(data)} 个可见元素\n")
    print(f"{'标签':<8}{'宽dp':>7}{'高dp':>7}{'x':>7}{'y':>7}  {'文字'}")
    print("-" * 62)
    for d in data:
        if not (d['interactive'] or d['text']):
            continue
        tag = d['tag'] + (('.' + d['cls']) if False else '')
        mark = '◆' if d['interactive'] else ' '
        print(f"{mark}{d['tag']:<7}{d['w']/DENS:>7.1f}{d['h']/DENS:>7.1f}"
              f"{d['x']/DENS:>7.1f}{d['y']/DENS:>7.1f}  {d['text'][:22]}")
    print("\n◆ = 可交互元素")
    # 只输出可交互元素的 JSON
    inter = [d for d in data if d['interactive']]
    with open('/data/workspace/dom_result.json', 'w') as f:
        json.dump(inter, f, ensure_ascii=False, indent=2)
    print(f"\n可交互元素 {len(inter)} 个已存 dom_result.json")
    return 0

if __name__ == '__main__':
    sys.exit(main())
