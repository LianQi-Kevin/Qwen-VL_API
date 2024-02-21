from argparse import ArgumentParser


def get_args():
    parser = ArgumentParser()
    parser.add_argument(
        "-c",
        "--checkpoint-path",
        type=str,
        default="Qwen/Qwen-VL-Chat-Int4",
        help="Checkpoint name or path, default to %(default)r",
    )
    parser.add_argument(
        "--server-port", type=int, default=8000, help="Demo server port."
    )
    parser.add_argument(
        "--server-name",
        type=str,
        default="127.0.0.1",
        help="Demo server name. Default: 127.0.0.1, which is only visible from the local computer."
             " If you want other computers to access your server, use 0.0.0.0 instead.",
    )

    return parser.parse_args()
