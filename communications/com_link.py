

class Link:

    def __init__(self, sckt, lname, rname):
        self.__sckt = sckt
        self.__lname = lname
        self.__rname = rname
        self.__sckt.connect(self.raddr)

    @property
    def laddr(self):
        return self.__sckt.getsockname()

    @property
    def raddr(self):
        return self.__sckt.getpeername()

    @property
    def lname(self):
        return self.__lname

    @property
    def rname(self):
        return self.__rname

    def receive(self):
        data = self.__sckt.recv(1024)
        print(f"{self.laddr} Received data from {self.raddr} : ")
        print(data)
        print()

    def __str__(self):
        out  = "Link{ \n"
        out += f"    Local ='{self.lname}'@{self.laddr} \n"
        out += f"    Remote='{self.rname}'@{self.raddr} \n"
        out += "}"
        return out