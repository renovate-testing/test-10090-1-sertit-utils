""" Script testing the file_utils """
import os
import tempfile

import numpy as np
from datetime import datetime, date
from sertit import files, misc
from CI.SCRIPTS import script_utils

FILE_DATA = os.path.join(script_utils.get_ci_data_path(), "file_utils")


def test_paths():
    """ Test path functions """
    curr_file = os.path.realpath(__file__)
    curr_dir = os.path.dirname(curr_file)
    with misc.chdir(curr_dir):
        # Relative path
        curr_rel_path = files.real_rel_path(curr_file, curr_dir)
        assert curr_rel_path == os.path.join(".", os.path.basename(__file__))

        # Abspath
        abs_file = files.to_abspath(curr_rel_path)
        assert abs_file == curr_file

        # Listdir abspath
        list_abs = files.listdir_abspath(curr_dir)
        assert curr_file in list_abs

        # Root path
        assert abs_file.startswith(files.get_root_path())


def test_archive():
    """ Test extracting functions """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Archives
        zip_file = os.path.join(FILE_DATA, "test_zip.zip")
        tar_file = os.path.join(FILE_DATA, "test_tar.tar")
        tar_gz_file = os.path.join(FILE_DATA, "test_targz.tar.gz")

        # Core dir
        core_dir = os.path.join(FILE_DATA, "core")
        folder = os.path.join(core_dir)
        archives = [zip_file, tar_file, tar_gz_file, folder]

        # Extract
        extracted_dirs = files.extract_files(archives, tmp_dir)

        # Test
        for ex_dir in extracted_dirs:
            script_utils.assert_dir_equal(core_dir, ex_dir)

        # Archive
        archive_base = os.path.join(tmp_dir, "archive")
        for fmt in ["zip", "tar", "gztar"]:
            archive_fn = files.archive(folder_path=core_dir,
                                       archive_path=archive_base,
                                       fmt=fmt)
            out = files.extract_file(archive_fn, tmp_dir)
            if fmt == "zip":
                script_utils.assert_dir_equal(core_dir, out)
            else:
                # For tar and tar.gz, an additional folder is created because these formats dont have any given file tree
                out_dir = files.listdir_abspath(out)[0]
                script_utils.assert_dir_equal(core_dir, out_dir)

            # Remove out directory in order to avoid any interferences
            files.remove(out)

        # Add to zip
        zip_out = archive_base + ".zip"
        core_copy = files.copy(core_dir, os.path.join(tmp_dir, "core2"))
        files.add_to_zip(zip_out, core_copy)

        # Extract
        unzip_out = os.path.join(tmp_dir, "out")
        files.extract_file(zip_out, unzip_out)

        # Test
        unzip_dirs = files.listdir_abspath(unzip_out)

        assert len(unzip_dirs) == 2
        script_utils.assert_dir_equal(unzip_dirs[0], unzip_dirs[1])


def test_get_file_name():
    """ Test get_file_name """
    file_name = files.get_file_name(__file__)
    assert file_name == "test_files"
    file_name = files.get_file_name(__file__ + "\\")
    assert file_name == "test_files"
    file_name = files.get_file_name(__file__ + "/")
    assert file_name == "test_files"


def test_cp_rm():
    """ Test CP/RM functions """
    with tempfile.TemporaryDirectory() as tmp_dir:
        empty_tmp = os.listdir(tmp_dir)

        # Copy file
        curr_path = os.path.realpath(__file__)
        file_1 = files.copy(curr_path, tmp_dir)
        file_2 = files.copy(curr_path, os.path.join(tmp_dir, "test_pattern.py"))

        # Copy dir
        dir_path = os.path.dirname(curr_path)
        test_dir = files.copy(dir_path, os.path.join(tmp_dir, os.path.basename(dir_path)))

        # Test copy
        assert os.path.isfile(file_1)
        assert os.path.isfile(file_2)
        assert os.path.isdir(test_dir)

        # Remove file
        files.remove(file_1)
        files.remove("non_existing_file.txt")
        files.remove_by_pattern(tmp_dir, name_with_wildcard="*pattern*", extension="py")

        # Remove dir
        files.remove(test_dir)

        # Assert tempfile is empty
        assert os.listdir(tmp_dir) == empty_tmp


def test_find_files():
    """ Test find_files """
    names = os.path.basename(__file__)
    root_paths = script_utils.get_proj_path()
    max_nof_files = 1
    get_as_str = True

    # Test
    path = files.find_files(names, root_paths, max_nof_files, get_as_str)

    assert path == os.path.realpath(__file__)


def test_json():
    """ Test json functions """
    test_dict = {"A": 3,
                 "C": "m2",  # Can be parsed as a date, we do not want that !
                 "D": datetime.today(),
                 "Dbis": date.today(),
                 "E": np.int64(15)}

    with tempfile.TemporaryDirectory() as tmp_dir:
        json_file = os.path.join(tmp_dir, "test.json")

        # Save pickle
        files.save_json(json_file, test_dict)

        # Load pickle
        obj = files.read_json(json_file)

        assert obj == test_dict


def test_pickle():
    """ Test pickle functions """

    test_dict = {"A": 3,
                 "B": np.zeros((3, 3)),
                 "C": "str",
                 "D": datetime.today(),
                 "E": np.int64(15)}

    with tempfile.TemporaryDirectory() as tmp_dir:
        pkl_file = os.path.join(tmp_dir, "test.pkl")

        # Save pickle
        files.save_obj(test_dict, pkl_file)

        # Load pickle
        obj = files.load_obj(pkl_file)

        # Test (couldn't compare the dicts as they contain numpy arrays)
        np.testing.assert_equal(obj, test_dict)


def test_get_file_in_dir():
    """ Test get_file_in_dir """
    # Get parent dir
    folder = os.path.dirname(os.path.realpath(__file__))

    # Test
    file = files.get_file_in_dir(folder, "file", ".py", filename_only=False, get_list=True, exact_name=False)
    filename = files.get_file_in_dir(folder, files.get_file_name(__file__), "py",
                                     filename_only=True, get_list=False, exact_name=True)

    assert file[0] == __file__
    assert filename == os.path.basename(__file__)


def test_hash_file_content():
    """ Test hash_file_content """
    file_content = "This is a test."

    # Test
    hashed = files.hash_file_content(file_content)

    # Test
    assert hashed == '16c5bf1fc5'
