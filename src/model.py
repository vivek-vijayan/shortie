# Model : URL
class URL:
    """
    A simple URL model class that encapsulates a URL string.

    This class serves as a basic container for a URL and provides a readable 
    representation for logging or debugging.
    """

    def __init__(self, url_string: str) -> None:
        """
        Initialize the URL object.

        Args:
            url_string (str): The URL string to store.
        """
        self.url = url_string

    def __repr__(self) -> str:
        """
        Return the string representation of the URL.

        Returns:
            str: The URL as a string.
        """
        return str(self.url)
