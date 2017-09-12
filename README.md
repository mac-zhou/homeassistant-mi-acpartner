# homeassistant-mi-acpartner

小米空调伴侣的homeassistant插件

本插件主要是对[homebridge-mi-acpartner](https://github.com/LASER-Yi/homebridge-mi-acpartner)移植到homeassistant

同时参考了 [HomeAssistant论坛](https://bbs.hassbian.com/)各路大神们几个空调插件的做法，此处不在一一全表

说到底，我只是个搬运工(^-^)
### Feature(功能）

* 开关空调

* 控制模式：

  - 使用空调码或红外码控制你的空调。
  - 在17-30度之间调整空调温度（默认情况）。
  - 温度如果调节到31度或者16度即是关闭空调。
  - 制冷，制热，自动模式支持。
  - 风力，扫风状态(目前只支持开/关)支持。
  - 目前暂时不支持自定义空调码，都是根据 homebridge-mi-acpartner 中 [presets.json](https://github.com/LASER-Yi/homebridge-mi-acpartner/blob/master/presets.json) 定义而来

### Config（配置）
* 配置说明

    * host: "空调伴侣的ip地址"

    * token: "空调伴侣的token"

    * name: 在HASS中显示的名字

    * target_temp: auto模式下设置的温度

    * target_sensor: "填写你的**温湿度传感器**ID"

* 配置示例

```yaml
climate:
    - platform: mi_acpartner
      name: mi_acpartner
      host: 10.0.0.234
      token: 8171378a40b1a77ee7a8254b15c75cfc
      target_sensor: sensor.temperature_158d00015aefc4
      target_temp: 26
```


