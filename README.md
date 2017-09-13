# homeassistant-mi-acpartner

小米空调伴侣的homeassistant插件

本插件主要是对[homebridge-mi-acpartner](https://github.com/LASER-Yi/homebridge-mi-acpartner)移植到homeassistant，感谢开发者。

同时参考了[HomeAssistant论坛](https://bbs.hassbian.com/)各路大神们几个空调插件的做法，此处不在一一全表，同样感谢。

说到底，我只是个搬运工(^-^)
### Feature(功能）

* 开关空调

* 控制模式：

  - 使用空调码或红外码控制你的空调。
  - 在17-30度之间调整空调温度（默认情况）。
  - 温度如果调节到31度或者16度即是关闭空调。
  - 制冷，制热，自动模式支持。
  - 风力，扫风状态(目前只支持开/关)支持。
  - 支持自定义风力(fan)和扫风(swing)的空调码或红外码，具体配置见下面可选配置部分。
  - 温度，模式不支持自定义空调码或红外码，根据 homebridge-mi-acpartner中[presets.json](https://github.com/LASER-Yi/homebridge-mi-acpartner/blob/master/presets.json) 定义而来

### Config（配置）
* 必要配置

    * host: 空调伴侣的ip地址

    * token: 空调伴侣的token

    * name: 在HASS中显示的名字

    * target_sensor: 获取当前温度，填写你的**温湿度传感器**ID （为了兼容某些用户无温湿度传感器，所以实际此项为可选配置）

* 可选配置

    * target_temp: 设置操作界面的起始温度（此配置项已经去除，老版本配置不影响）

    * sync: 填写与空调伴侣的同步间隔，单位是秒（默认是15秒）

    * customize：自定义风力或扫风空调码或红外码

* 配置示例

基本配置
```yaml
climate:
    - platform: mi_acpartner
      name: mi_acpartner
      host: 10.0.0.234
      token: 8171378a40b1a77ee7a8254b15c75cfc
      target_sensor: sensor.temperature_158d00015aefc4
```

自定义空调码或红外码

大部分空调码以01开头；大部分红外码以FE开头，支持混写。
```yaml
climate:
  - platform: mi_acpartner
    name: mi_acpartner
    host: 10.0.0.234
    token: 1378a40b1a77ee7a8254b15c75cfb
    target_sensor: sensor.temperature_158d00015a
    sync: 60
    customize:
      swing:
        top: 010501820000261801
        down: FEADASDSDSDSDSDSADSAFADSFASA
      fan:
        max: FEADASDSDSDSDSDSADSAFADSFASAD
        med: FEBDASDSDSDSDSDSADSAFADSFASAR
        min: 010501A20000261B01
```

