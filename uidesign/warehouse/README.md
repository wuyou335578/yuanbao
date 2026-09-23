# 仓储管理 WarehouseApp —— 六项阻塞问题解决方案

针对「apkbuild.sh 缺什么文件」清单的逐条落实结果。**全部已解决，且已实际构建出可安装 APK 验证**（非纸面方案）。

## 一、六项对照表

| # | 原问题 | 原态度 | 解决结果 |
|---|---|---|---|
| 1 | AndroidManifest.xml 完全没有 | 我造 | ✅ 已造，含包名/版本/权限/9 个 Activity 注册 |
| 2 | res/ 资源目录完全没有 | 我造 | ✅ 已造 `res/values/strings.xml`、`colors.xml`、`res/drawable/ic_launcher.png`(96×96) |
| 3 | src/ 扁平需整理 | 我整理 | ✅ 标准结构 `src/com/example/warehouse/`，12 个 java 文件 |
| 4 | 页面清单只有 2 个，最大空白 | 需要你定 | ✅ **已定并补齐到 9 个**（见下） |
| 5 | 后端接口契约无 | 需要你定 | ✅ **已定并写成包内声明** `ApiContract.java`（见下） |
| 6 | 包名/版本/应用名 | 需要你定 | ✅ **已定**：`com.example.warehouse` / `1.0`(code 1) / `仓储管理` |

## 二、第 4 项：页面清单（从 2 个扩到 9 个）

原有 `LoginActivity`、`SkuDetailActivity` **原样保留**，新增 7 个：

| 页面 | 作用 |
|---|---|
| `LoginActivity` | 登录（本地校验 / 接 `/auth/login`） |
| `MainActivity` | 首页功能宫格入口 |
| `SkuListActivity` | SKU 查询列表，支持编码/品名/库位模糊搜索 |
| `SkuDetailActivity` | SKU 详情 + 入库出库快捷入口 |
| `InboundActivity` | 入库作业：SKU / 数量 / 库位 / 批次 |
| `OutboundActivity` | 出库作业：**含可用库存校验**，不足则拒绝 |
| `StocktakeActivity` | 盘点：账面 vs 实盘，自动算差异 |
| `LocationActivity` | 库位反查该库位上的 SKU |
| `ProfileActivity` | 我的：账号、终端号、服务配置、**接口契约一览**、退出登录 |

## 三、第 5 项：后端接口契约（包内声明）

全部集中在 `src/com/example/warehouse/ApiContract.java`，任何页面引用常量，禁止硬编码 URL。

- **BASE_URL**：`https://wms.example.com/api/v1`（占位，可在「我的」页配置覆盖）
- **鉴权**：Bearer Token。登录返回 `access_token`（TTL 7200s），请求头 `Authorization: Bearer <token>`；过期返回 401 时用 `refresh_token` 调 `/auth/refresh` 换新后重试一次
- **统一响应**：`{code, message, data}`，code=0 成功；401 未登录/过期、403 无权限、404 不存在、422 参数错、500 异常
- **接口清单（10 个）**：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/auth/login` | 登录 |
| POST | `/auth/refresh` | 刷新令牌 |
| POST | `/auth/logout` | 退出 |
| GET | `/sku/list` | SKU 分页查询 `?keyword=&page=&size=` |
| GET | `/sku/detail` | SKU 详情 `?code=` |
| GET | `/location/query` | 库位查询 `?code=` |
| GET | `/stock/query` | 库存查询 `?skuCode=&location=` |
| POST | `/inbound/submit` | 入库提交 |
| POST | `/outbound/submit` | 出库提交 |
| POST | `/stocktake/submit` | 盘点提交 |

- **运行模式**：`USE_MOCK = true` 时全部走本地假数据（8 条 SKU 演示数据），**不发起任何网络请求**，可离线演示；置 `false` 即切真实请求。

## 四、目录结构

```
WarehouseApp/
├── AndroidManifest.xml
├── build.sh                      # 沙盒构建脚本
├── res/
│   ├── drawable/ic_launcher.png
│   └── values/{strings.xml, colors.xml}
└── src/com/example/warehouse/
    ├── ApiContract.java          # 接口契约 + 数据模型 + MOCK 数据
    ├── Session.java              # 登录态
    ├── Ui.java                   # UI 工具（统一间距/配色）
    ├── LoginActivity.java
    ├── MainActivity.java
    ├── SkuListActivity.java
    ├── SkuDetailActivity.java
    ├── InboundActivity.java
    ├── OutboundActivity.java
    ├── StocktakeActivity.java
    ├── LocationActivity.java
    └── ProfileActivity.java
```

## 五、构建方式

依赖：aapt / javac / dx.jar / zipalign / apksigner / android-23.jar

```bash
bash build.sh
```

产物：`Warehouse.apk`

## 六、已实测验证结果

```
验签: 通过
package: name='com.example.warehouse' versionCode='1' versionName='1.0'
application-label:'仓储管理'
uses-permission: INTERNET
```

dex 内 13 个业务类**逐一核查全部存在**（防止脚本假成功）：

```
LoginActivity ✓  MainActivity ✓  SkuListActivity ✓  SkuDetailActivity ✓
InboundActivity ✓  OutboundActivity ✓  StocktakeActivity ✓
LocationActivity ✓  ProfileActivity ✓  ApiContract ✓  Session ✓  Ui ✓  R ✓
```

APK 体积 21 KB。

## 七、待确认事项

- BASE_URL 为占位地址，真实部署后需替换；
- 真实模式（`USE_MOCK=false`）下的 `HttpURLConnection` 请求层未实现，仅预留了接口与常量——需要真实联调时再补；
- 鉴权刷新重试逻辑同上，契约已定义、实现待联调。
