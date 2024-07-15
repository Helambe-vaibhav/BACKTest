from OP_BackTest.core import CreateDB
from pathlib import Path

if __name__ == '__main__':
    root_path = Path(__file__).parent
    print(root_path)
    data_folder = 'data_folder'
    data_folder = root_path / data_folder
    db_path = 'OP_BackTest/DataDB/data.db'
    db_path = root_path / db_path
    db = CreateDB(data_folder, db_path)
    db.run()
