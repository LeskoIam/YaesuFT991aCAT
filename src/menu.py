# Documentation is like sex.
# When it's good, it's very good.
# When it's bad, it's better than nothing.
# When it lies to you, it may be a while before you realize something's wrong.


class Menu:

    def __init__(self):
        self.MENU_ITEMS = self.__load_menu_items()

    def get_menu_function(self, num):
        return self.__find_item(num)

    def __find_item(self, num):
        return [item for item in self.MENU_ITEMS if item.num == num][0]

    @staticmethod
    def __load_menu_items():
        with open(r"D:\Lesko\workspace\ham\Yaesu991aCAT\src\menu.csv", "r") as menu_file:
            data = menu_file.read()
        data = data.split("\n")
        out = []
        for line in data:
            if line.startswith("P1;"):
                continue
            item = line.split(";")
            item = MenuFunction(
                int(item[0]),
                item[1],
                item[2],
                int(item[3] if item[3] != "-" else 0)
            )
            out.append(item)
        return out


class MenuFunction:

    def __init__(self, num, description, param_description, digits):
        self.num = num
        self.function = description
        self.param_description = param_description
        self.digits = digits

    def __repr__(self):
        return f"<num: {self.num } function: '{self.function}' " \
               f"param_description: '{self.param_description}' digits: {self.digits}>"

    def format_param(self, param):
        param = str(param).rjust(self.digits, "0")
        return f"{self.read_command()}{param}"

    def read_command(self):
        return f"{self.num:0>3}"


if __name__ == '__main__':

    m = Menu()
    print(m.get_menu_function(6).format_param("A"))
