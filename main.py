# coding:utf-8
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from pykeepass import PyKeePass
import config, os

dir_path = os.path.dirname(__file__)

class DemoExtension(Extension):
    def __init__(self):
        super(DemoExtension, self).__init__()
        self.db = None
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        reload(config)
        try:
            if config.database_path == "" or config.master_key == "":
                raise ValueError("您尚未配置数据库路径或密码，请按回车配置")
            try:
                extension.db = PyKeePass(config.database_path, password=config.master_key)
            except:
                raise IOError("数据库或密码错误,回车后请重新配置")
            arg = event.get_argument()
            args_list = None
            try:
                args_list = arg.split(" ")
            except:
                pass
            if len(args_list) >= 1:
                arg = args_list[0]
                if arg == "add":
                    return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                                       name='%s' % "添加密码到数据库",
                                                                       on_enter=ExtensionCustomAction(args_list, keep_app_open=True))])
                else:
                    if len(args_list) > 1:
                        raise AttributeError("参数填写错误")
                    # 执行密码查询
                    items = []
                    for e in extension.db.entries:
                        title = e.title
                        name = e.username
                        if title is None:
                            title = ""
                        if name is None:
                            name = ""
                        if arg in title or arg in name:
                            items.append(ExtensionResultItem(icon='images/icon.png',
                                                             name='%s' % title,
                                                             description='%s' % name,
                                                             on_enter=CopyToClipboardAction(e.password)))
                    return RenderResultListAction(items)

        except (ValueError, IOError, AttributeError), e:
            print type(e)
            return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                               name='%s' % e.message,
                                                               on_enter=ExtensionCustomAction(e, keep_app_open=True))])


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        data = event.get_data()
        # 数据库路径没配置
        if isinstance(data, ValueError):
            os.system("gedit " + os.path.join(dir_path, "config.py"))
        # 数据库路径或密码没验证成功
        if isinstance(data, IOError):
            os.system("gedit " + os.path.join(dir_path, "config.py"))
        # 参数填写错误
        if isinstance(data, AttributeError):
            pass
        # 添加密码
        if isinstance(data, list):
            print data, extension.db
            if len(data) != 4:
                return RenderResultListAction([ExtensionResultItem(icon='images/icon.png',
                                                                   name='%s' % "参数填写错误",
                                                                   on_enter=DoNothingAction())])
            else:
                title = data[-3]
                username = data[-2]
                pwd = data[-1]
                groups = extension.db.groups
                if len(groups) == 1:
                    extension.db.add_entry(groups[0], title, username, pwd)
                    extension.db.save()
                else:
                    extension.db.add_entry(groups[1], title, username, pwd)
                    extension.db.save()
                os.system("notify-send -i " + os.path.join(os.path.join(dir_path, "images"), "icon.png") +
                          " 'KeePass' '密码添加成功'")


# 开始
if __name__ == '__main__':
    DemoExtension().run()
