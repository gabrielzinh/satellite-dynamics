from enum import Enum;
import configparser, requests, json;
Urlbase = "https://www.space-track.org";

class DataExtractor:
    class SpaceTrackDatabases(Enum):
        LATEST_RECORDS = "gp";
        HIST_RECORDS = "gp_history";

    class SearchFields(Enum):
        ORIGINATOR = "ORIGINATOR";
        OBJECT_NAME = "OBJECT_NAME";
        OBJECT_ID = "OBJECT_ID";
        CLASSIFICATION_TYPE = "CLASSIFICATION_TYPE";
        NORAD_CAT_ID = "NORAD_CAT_ID";
        LAUNCH_DATE = "LAUNCH_DATE";
        DECAY_DATE = "DECAY_DATE";
        EPOCH = "EPOCH";

    class Operators(Enum):
        GREATER_THAN = ">";
        LESS_THAN = "<";
        EQUAL = "";
        NOT_EQUAL = "<>"
        RANGE = "--";
        LIKE = "~~";

    class SpecialValues(Enum):
        NULL = "null-val";

    class ConnectionError(Exception):
        def __init___(self, args):
            Exception.__init__(self, f"Login Exception was raised with arguments {args}");
            self.args = args;

    @staticmethod
    def SpaceTrackQuery(constraint_array, database, file_name, order_by = SearchFields.EPOCH, asc_sort = 1, limit = None, save_data = True):
        if (database != DataExtractor.SpaceTrackDatabases.LATEST_RECORDS or database != DataExtractor.SpaceTrackDatabases.HIST_RECORDS):
            database = DataExtractor.SpaceTrackDatabases.HIST_RECORDS;

        RequestLogin = "/ajaxauth/login";
        RequestCmdAction = f"/basicspacedata/query/class/{database.value}";
        LinkConstraints = "";
        LinkSortLimit = "";

        for Constraint in constraint_array:
            Field, Operator, Value = Constraint[0], Constraint[1], "";
            String = "";

            if (Operator == DataExtractor.Operators.RANGE):
                for val in Constraint[2 : : 2]:
                    NextValue = Constraint[Constraint.index(val) + 1];
                    Value += f"{str(val)}{Operator.value}{str(NextValue)},";

                Value = Value[: -1];
                String += f"/{Field.value}/{Value}";

            elif (Operator == DataExtractor.Operators.LIKE or Operator == DataExtractor.Operators.EQUAL):
                for val in Constraint[2 :]:
                    Value += f"{Operator.value}{str(val).upper()},";

                Value = Value[: -1];
                String += f"/{Field.value}/{Value}";

            else:
                Value = str(Constraint[2]);
                String += f"/{Field.value}/{Operator.value}{Value}";

            LinkConstraints += String;

        LinkSortLimit += f"/orderby/{order_by.value} {"asc" if (asc_sort == 1) else "desc"}";

        if (limit is not None and type(limit) is int):
            LinkSortLimit += f"/limit/{str(limit)}/format/json";

        Config = configparser.ConfigParser();
        Config.read("STCredentials.ini");
        Username = Config.get("configuration", "username");
        Password = Config.get("configuration", "password");
        Credentials = {"identity": Username, "password": Password};
        CompleteLink = Urlbase + RequestCmdAction + LinkConstraints + LinkSortLimit;
        Data = None;

        with requests.Session() as session:
            Response = session.post(Urlbase + RequestLogin, data = Credentials);

            if (Response.status_code != 200):
                print(Response);
                raise ConnectionError(Response, "POST fail on login");

            Response = session.get(CompleteLink);

            if (Response.status_code != 200):
                print(Response);
                raise ConnectionError(Response, "GET fail on request for objects");

            Data = json.loads(Response.text);

            if (save_data == True):
                if (file_name.find(".") != -1):
                    file_name = file_name.partition(".")[0];

                with open(f"{file_name}.json", "w") as file:
                    json.dump(Data, file, ensure_ascii = True, indent = 4);

        return Data;