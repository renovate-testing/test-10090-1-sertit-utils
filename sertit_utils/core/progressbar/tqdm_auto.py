from tqdm.auto import tqdm


def progressbar(iterable, **kwargs):
    return tqdm(iterable, **kwargs)
