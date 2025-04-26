import pandas as pd

from new_client_integ.utils import select_rows_by_dict


class BaseDataLoader:
    def __init__(self, config):
        self.config = config

    def load(self, file_path):
        raise NotImplementedError("Subclasses should implement this method.")


class CSVDataLoader(BaseDataLoader):
    def __init__(self, config):
        super().__init__(config)

    def load(self, file_path):
        """
        Load data from a CSV file and filter it based on the provided configuration.
        :param file_path:
        :return:
        """
        data = pd.read_csv(file_path)
        filt_data = select_rows_by_dict(data, self.config["filter_by"])
        items_list = list(filt_data[self.config["name_column"]].unique())
        items_list = [item.strip() for item in items_list]
        items_list = list(set(items_list))
        return items_list


if __name__ == '__main__':
    filename = "D:\\Projects\\Kaufmann_and_Co\\ingredients_matching\\new_client.csv"
    cfg = {
        "filter_by": {"מוצר בסיס/ חומר גלם": "חומר גלם"},
        "name_column": "שם הרכיב",
    }
    loader = CSVDataLoader(cfg)
    items = loader.load(filename)
    print(items)
