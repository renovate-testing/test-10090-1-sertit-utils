import arcpy  # pylint: disable=import-error


class __ArcpyProgressBar(object):

    def __init__(self, generator, **kwargs):
        if not hasattr(generator, '__len__'):
            raise Exception(f"Generator {generator} must have attribute len()")
        self.generator = generator
        arcpy.SetProgressor(
            "step", min_range=0, max_range=len(generator), step_value=1
        )
        self.curr_i = 0

    def __iter__(self):
        return self

    def __len__(self):
        return len(self.generator)

    # Python 3
    def __next__(self):
        return self.next()

    # Python 2
    def next(self):
        arcpy.SetProgressorPosition()
        elem = next(self.generator)
        self.curr_i + 1
        if self.curr_i == len(self.generator):
            arcpy.ResetProgressor()
        return elem


def progressbar(iterable, **kwargs):
    return __ArcpyProgressBar(iterable, **kwargs)