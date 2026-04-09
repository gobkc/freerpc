freerpc目录结构

````yaml
main.py: 入口

app:
  __init__.py:
  app.py: 应用初始化

context:
  app_context.py: 上下文(目前只携带配置信息)

ui:
  __init__.py:
  main_window.py: 主窗口
  header_bar.py: 顶部 toolbar
  left_panel.py: 左侧（proto + API）
  center_panel.py: 中间（请求）
  right_panel.py: 右侧（结果）
  json_tree.py: 左侧菜单组件
  editable_json_tree.py: 请求参数和metadata参数编辑控件

handlers:
  __init__.py:
  toolbar_handler.py: toolbar事件
  api_handler.py: API点击事件

services:
  __init__.py:
  grpc_service.py: gRPC调用（预留）
  proto_service.py: proto解析（预留）

styles:
  style.css: GTK样式

utils:
  __init__.py:
  json_utils.py: JSON格式化
  config_manager.py: 配置管理器
````
