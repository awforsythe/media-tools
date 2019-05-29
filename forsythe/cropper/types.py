import enum


class Corner(enum.Enum):
    top_left = 0
    top_right = 1
    bottom_left = 2
    bottom_right = 3


class Edge(enum.Enum):
    left = 0
    right = 1
    top = 2
    bottom = 3

    @property
    def vertical(self):
        return self == self.top or self == self.bottom

    @property
    def corners(self):
        return {
            self.left: (Corner.top_left, Corner.bottom_left),
            self.right: (Corner.top_right, Corner.bottom_right),
            self.top: (Corner.top_left, Corner.top_right),
            self.bottom: (Corner.bottom_left, Corner.bottom_right),
        }[self]
