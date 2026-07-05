# ⚡️ 国家电网电力获取 · HA Add-on 版

[![Docker Image CI](https://github.com/wuwweizn/sgcc_electricity_new/actions/workflows/docker-image.yml/badge.svg)](https://github.com/wuwweizn/sgcc_electricity_new/actions/workflows/docker-image.yml)

> 本仓库 Fork 自 [ARC-MX/sgcc_electricity_new](https://github.com/ARC-MX/sgcc_electricity_new)，在其基础上针对 **Home Assistant Add-on** 使用场景做了专项修复，在此感谢原作者的贡献。

<p align="center">
<img src="assets/image-20230730135540291.png" alt="mini-graph-card" width="400">
<img src="assets/image-20240514.jpg" alt="mini-graph-card" width="400">
</p>

---

## 此分支修复内容

| 问题 | 修复 |
|------|------|
| Chrome 150 在 HA OS 容器中崩溃（`session not created`） | 固定使用 Chrome for Testing **120.0.6099.109**（仅 amd64），彻底解决崩溃 |
| 腾讯风控 RK001 登录被拦截 | CDP 注入反指纹脚本，伪装为 Windows Chrome 136，绕过容器指纹检测 |
| 验证码控件检测到隐藏的预加载 DOM 元素 | 改用 `visibility_of_element_located` 替代 `presence_of_element_located` |
| 风控触发时自动切换二维码登录 | 检测到 RK001 → 自动切换二维码模式，通过 HA 持久通知展示二维码 |
| 二维码无法送达（PushPlus 需要实名认证） | 改用 HA 自带的通知系统：图片保存至 `/config/www/`，HA 界面直接显示 |
| GitHub Actions 推送镜像权限不足 | 使用 `CR_PAT` Personal Access Token，禁用 provenance/sbom 附件 |

---

## 简介

通过 Python Selenium 自动化获取国家电网官网的电费、电量数据，接入 Home Assistant 实体。登录时的腾讯点击/滑块验证码通过**大模型（LLM）视觉识别**自动解算，无需人工干预；若遭遇风控拦截则自动切换二维码登录并通过 **HA 通知**推送二维码图片。

**提供以下 HA 实体：**

| 实体 | 说明 |
|------|------|
| `sensor.last_electricity_usage_xxxx` | 最近一天用电量（kWh） |
| `sensor.electricity_charge_balance_xxxx` | 电费余额 / 上月应交电费（元） |
| `sensor.yearly_electricity_usage_xxxx` | 今年总用电量（kWh） |
| `sensor.yearly_electricity_charge_xxxx` | 今年总电费（元） |
| `sensor.month_electricity_usage_xxxx` | 最近一月用电量（kWh） |
| `sensor.month_electricity_charge_xxxx` | 上月总电费（元） |
| `sensor.month_valley_usage_xxxx` | 当月谷时用电量（kWh） |
| `sensor.month_flat_usage_xxxx` | 当月平时用电量（kWh） |
| `sensor.month_peak_usage_xxxx` | 当月峰时用电量（kWh） |
| `sensor.month_tip_usage_xxxx` | 当月尖时用电量（kWh） |
| `sensor.prepay_balance_xxxx` | 预付费余额 / 应交金额（元） |

**适用范围**：除南方电网覆盖省份（广东、广西、云南、贵州、海南）外的用户。

**支持架构**：
- `linux/amd64`：x86-64，使用 Chrome for Testing 120（已修复崩溃问题）
- `linux/arm64`：树莓派 3+、N1 盒子等，使用系统 Chromium

---

## 安装方式：HA Add-on（推荐）

### 1. 添加仓库

在 Home Assistant 中依次进入：**设置 → 加载项 → 加载项商店 → 右上角菜单 → 仓库**

添加以下地址：

```
https://github.com/wuwweizn/sgcc_electricity_new
```

### 2. 安装加载项

仓库添加成功后，在加载项商店搜索 **SGCC Electricity**，点击安装，等待镜像拉取完成（镜像来自 `ghcr.io`）。

### 3. 获取大模型 API Key

本项目使用大模型自动解算腾讯验证码，需要配置 LLM API。

推荐使用**火山引擎豆包**（注册即赠免费额度，个人使用基本免费）：

1. 注册 [火山引擎](https://www.volcengine.com/) 并完成实名认证
2. 进入 [火山方舟控制台](https://console.volcengine.com/ark) → 在线推理 → 创建推理接入点
   - 选择模型：`Doubao-Seed-2.0-pro-260215`（或其他多模态视觉模型）
   - 记录生成的**接入点 ID**（格式：`ep-2025xxxxxx-xxxxx`）
3. 左侧菜单 → API Key 管理 → 创建并复制 API Key

也可使用其他兼容 OpenAI 接口的视觉模型（GPT-4o、Claude 等），自行配置 `LLM_BASE_URL` 和 `LLM_MODEL`。

### 4. 获取 HA 长期访问令牌

HA 界面 → 左下角个人头像 → 安全 → 长期访问令牌 → 创建令牌，复制保存。

### 5. 配置加载项

在加载项的「配置」页面填写以下参数：

| 参数 | 说明 |
|------|------|
| `PHONE_NUMBER` | 国网登录手机号 |
| `PASSWORD` | 国网登录密码 |
| `HASS_URL` | HA 地址，如 `http://homeassistant.local:8123/` |
| `HASS_TOKEN` | 上一步获取的长期访问令牌 |
| `LLM_API_KEY` | 大模型 API Key |
| `LLM_BASE_URL` | 大模型接口地址（火山引擎留空使用默认值） |
| `LLM_MODEL` | 模型名称，如 `ep-2025xxxxxx-xxxxx`（火山引擎接入点 ID） |
| `JOB_START_TIME` | 每日执行时间，默认 `07:00`，每 12 小时执行一次 |
| `IGNORE_USER_ID` | 需要忽略的户号，多个用英文逗号分隔 |
| `BALANCE` | 余额低于此值时触发通知（元） |

### 6. 启动加载项

保存配置后，启动加载项，查看日志确认运行正常。正常运行的日志类似：

```
Google Chrome for Testing 120.0.6099.109
ChromeDriver 120.0.6099.109
浏览器驱动已初始化。
打开登录页面: https://95598.cn/osgweb/login
通过点击验证码登录成功。
用户 [xxxxxxx] 数据获取完成: 余额=xxx元, 最近日用电=xxx度
```

---

## 二维码登录说明

若遭遇腾讯风控拦截（RK001 错误），加载项会**自动切换二维码登录模式**：

1. 二维码图片保存至 `/config/www/sgcc_login_qr.png`
2. HA 界面左下角铃铛出现红点通知，标题为「⚡ 国网需要扫码登录」
3. 点开通知，用**国家电网 App** 扫描二维码即可
4. 加载项默认等待 **180 秒**，请在此时间内完成扫码

> 二维码 Session 通常持续 7～30 天，无需频繁扫码。

---

## HA 数据展示

配置 `configuration.yaml`（将 `_xxxx` 替换为日志中实际的户号后缀）：

```yaml
template:
  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.electricity_charge_balance_xxxx
    sensor:
      - name: electricity_charge_balance_xxxx
        unique_id: electricity_charge_balance_xxxx
        state: "{{ states('sensor.electricity_charge_balance_xxxx') }}"
        state_class: measurement
        unit_of_measurement: "CNY"
        device_class: monetary

  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.last_electricity_usage_xxxx
    sensor:
      - name: last_electricity_usage_xxxx
        unique_id: last_electricity_usage_xxxx
        state: "{{ states('sensor.last_electricity_usage_xxxx') }}"
        state_class: measurement
        unit_of_measurement: "kWh"
        device_class: energy

  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.yearly_electricity_usage_xxxx
    sensor:
      - name: yearly_electricity_usage_xxxx
        unique_id: yearly_electricity_usage_xxxx
        state: "{{ states('sensor.yearly_electricity_usage_xxxx') }}"
        state_class: total_increasing
        unit_of_measurement: "kWh"
        device_class: energy

  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.yearly_electricity_charge_xxxx
    sensor:
      - name: yearly_electricity_charge_xxxx
        unique_id: yearly_electricity_charge_xxxx
        state: "{{ states('sensor.yearly_electricity_charge_xxxx') }}"
        state_class: total_increasing
        unit_of_measurement: "CNY"
        device_class: monetary

  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.month_electricity_usage_xxxx
    sensor:
      - name: month_electricity_usage_xxxx
        unique_id: month_electricity_usage_xxxx
        state: "{{ states('sensor.month_electricity_usage_xxxx') }}"
        state_class: measurement
        unit_of_measurement: "kWh"
        device_class: energy

  - trigger:
      - platform: event
        event_type: state_changed
        event_data:
          entity_id: sensor.month_electricity_charge_xxxx
    sensor:
      - name: month_electricity_charge_xxxx
        unique_id: month_electricity_charge_xxxx
        state: "{{ states('sensor.month_electricity_charge_xxxx') }}"
        state_class: measurement
        unit_of_measurement: "CNY"
        device_class: monetary
```

配置完成后重启 HA。

结合 [mini-graph-card](https://github.com/kalkih/mini-graph-card) 可实现可视化效果：

```yaml
type: vertical-stack
cards:
  - type: custom:mini-graph-card
    entities:
      - entity: sensor.last_electricity_usage_xxxx
        name: 国网每日用电量
        aggregate_func: first
        show_state: true
        show_points: true
        icon: mdi:lightning-bolt-outline
      - entity: sensor.electricity_charge_balance_xxxx
        name: 电费余额
        aggregate_func: first
        show_state: true
        show_points: true
        color: "#e74c3c"
        icon: mdi:cash
        y_axis: secondary
    group_by: date
    hour24: true
    hours_to_show: 240
```

---

## 更新日志

- **2026-07-06**：Fork 自 ARC-MX 分支，针对 HA Add-on 场景专项修复：
  - 固定 Chrome for Testing 120.0.6099.109（解决 Chromium 150 在 HA OS 中崩溃）
  - CDP 反指纹注入（解决 RK001 腾讯风控拦截）
  - 验证码隐藏元素检测修复
  - 二维码登录通知改用 HA 持久通知（告别 PushPlus 实名认证）
  - GitHub Actions 自动构建并推送至 ghcr.io
- **2025-05-20**（原仓库）：弃用 CloakBrowser，改用原生 Selenium + Chrome 反检测方案
- **2025-05-01**（原仓库）：验证码识别升级为大模型（LLM）视觉方案
- **2025-01-05**（原仓库）：新增 HA Add-on 部署方式
- **2024-12-10**（原仓库）：新增 `IGNORE_USER_ID` 忽略指定户号
- **2024-07-05**（原仓库）：新增余额不足提醒功能
- **2024-07-03**（原仓库）：新增每天执行两次，支持 7/30 天历史数据
- **2024-06-13**（原仓库）：SQLite 替换 MongoDB

---

## 致谢

- 原始作者：[louisslee/sgcc_electricity](https://github.com/louisslee/sgcc_electricity)
- 主要维护：[ARC-MX/sgcc_electricity_new](https://github.com/ARC-MX/sgcc_electricity_new)
- 本分支维护：[wuwweizn/sgcc_electricity_new](https://github.com/wuwweizn/sgcc_electricity_new)
