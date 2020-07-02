# wx_third_part_platform
微信第三方平台
flask 版本v0.5
fastapi 版本v0.75

# 队列
想要更改为 tools, worker协作的模式, 本体就作为一个队列以及状态库

## 工作模式
收到消息, 塞入消息队列,分配任务编号
workers 从消息队列中拿到, 将处理结果放到内存库,修改状态已完成
根据编号获取结果, 返回
