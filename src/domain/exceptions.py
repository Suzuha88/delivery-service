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
            self.description = "Couldn't find a single package with these constraints}"
        self.description = (
            "Couldn't find a package with this id, please check if id is correct"
        )
