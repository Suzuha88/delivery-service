class MyError(Exception):
    def __init__(self) -> None:
        self.description = ""

    def __str__(self) -> str:
        return self.description


class PackageIsPendingError(MyError):
    def __init__(self) -> None:
        self.description = "Package registration is pending, please try again later"


class PackageNotFoundError(MyError):
    def __init__(self, multiple: bool = False) -> None:
        if multiple:
            self.description = "Packages not found}"
        self.description = "Package not found"
