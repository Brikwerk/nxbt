def replace_subarray(arr, start, num_elms, value=0, replace_arr=None):
    """Replaces a subsection within an array with another
    set of values.

    :param arr: The array to replace values within
    :type arr: list
    :param start: The starting index for replacement
    :type start: int
    :param num_elms: The number of elements to be replaced
    :type num_elms: int
    :param value: The value to replace elements within the
    subarray with, defaults to 0
    :type value: any, optional
    :param replace_arr: A subarray to insert within
    the passed array, defaults to None
    :type replace_arr: list, optional
    """

    if replace_arr:
        arr[start:start + num_elms] = replace_arr
    else:
        arr[start:start + num_elms] = [value] * num_elms


def format_message(data, split, name):
    """Formats a given byte message in hex format split
    into payload and subcommand sections.

    :param data: A series of bytes
    :type data: bytes
    :param split: The location of the payload/subcommand split
    :type split: integer
    :param name: The name featured in the start/end messages
    :type name: string
    :return: The formatted data
    :rtype: string
    """

    payload = ""
    subcommand = ""
    for i in range(0, len(data)):
        data_byte = str(hex(data[i]))[2:].upper()
        if len(data_byte) < 2:
            data_byte = "0" + data_byte
        if i <= split:
            payload += "0x" + data_byte + " "
        else:
            subcommand += "0x" + data_byte + " "

    formatted = (
        f"--- {name} Msg ---\n" +
        f"Payload:    {payload}\n" +
        f"Subcommand: {subcommand}")

    return formatted


def format_msg_controller(data):
    """Prints a formatted message from a controller

    :param data: The bytes from the controller message
    :type data: bytes
    """

    return format_message(data, 13, "Controller")


def format_msg_switch(data):
    """Prints a formatted message from a Switch

    :param data: The bytes from the Switch message
    :type data: bytes
    """

    return format_message(data, 10, "Switch")
