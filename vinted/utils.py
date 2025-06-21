import re

from .exceptions import InvalidUrlException
from urllib.parse import unquote


def parse_url_to_params(url: str):
    try:
        # Decode the URL
        decoded_url = unquote(url)

        # Match the domain part
        matched_params = re.match(r"^https:\/\/www\.vinted\.([a-z]+)", decoded_url)
        if not matched_params:
            raise InvalidUrlException

        # Define the missing IDs parameters
        missing_ids_params = ["catalog", "status"]

        # Match the parameters in the URL
        params = re.findall(r"([a-z_]+)(\[\])?=([a-zA-Z 0-9._À-ú+%]*)&?", decoded_url)
        if not isinstance(matched_params.groups(), tuple):
            raise InvalidUrlException

        # Initialize a dictionary to store mapped parameters
        mapped_params = {}

        for param_name, is_array, param_value in params:
            # Replace spaces with '+' in param_value if they exist
            if " " in param_value:
                param_value = param_value.replace(" ", "+")

            # Handle array parameters
            if is_array:
                if param_name in missing_ids_params:
                    param_name = f"{param_name}_id"

                key_name = param_name if param_name.endswith("s") else f"{param_name}s"

                if key_name in mapped_params:
                    mapped_params[key_name].append(param_value)
                else:
                    mapped_params[key_name] = [param_value]

            else:
                mapped_params[param_name] = param_value

        # Construct the final parameters as a query string
        final_params = {}
        for key, value in mapped_params.items():
            if isinstance(value, list):
                final_params[key] = ",".join(value)
            else:
                final_params[key] = value

        # Remove time, page and per_page parameters from final dictionary
        [
            final_params.pop(key)
            for key in ["time", "page", "per_page"]
            if key in final_params.keys()
        ]

        return final_params
    except Exception as e:
        print(e)
        raise InvalidUrlException
