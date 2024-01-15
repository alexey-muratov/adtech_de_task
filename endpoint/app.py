import json
from flask import Flask, request
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

db_host = os.environ["DB_HOST"]
db_port = os.environ["DB_PORT"]
db_database = os.environ["DB_DATABASE"]
db_user = os.environ["DB_USER"]
db_password = os.environ["DB_PASSWORD"]
db_schema = os.environ["DB_SCHEMA"]
db_table = os.environ["DB_TABLE"]


@app.route("/")
def route():
    return "Status: OK"


@app.route("/event", methods=["POST"])
def addEvent():
    "Add data about a new event to the database"

    if request.method == "POST":

        # 1. Get the request body
        body_json = request.get_json()

        # 2. Verify the parameters
        
        # 2.1. Check that all required parameters are specified
        for event_property in ["id", "event_date", "metric1", "metric2"]:
            if event_property not in body_json.keys():
                return "Error: " + event_property + " is required", 405

        # 2.2. Check the type of parameters
        prop_required_types = \
            {"id": int, "attribute1": int, "attribute2": int, "attribute3": int, "attribute4": str,
             "attribute5": str, "attribute6": bool, "metric1": int, "metric2": float}
        for item in body_json.items():
            if (item[0] != "event_date") \
            and not (isinstance(item[1], prop_required_types[item[0]])):
                return "Error: " + item[0] + " has an incorrect type", 405
            elif item[0] == "event_date":
                try:
                    datetime.strptime(body_json[item[0]], "%Y-%m-%dT%H:%M:%S")
                except:
                    return "Error: The format for " + item[0] + " is incorrect", 405
        
        # 3. If we reached this point, create SQL INSERT statement.
        #    Function process_type() is used to join properties of different types
        #    into a single SQL-compliant string
        def process_type(x):
            if isinstance(x, str):
                return "'" + x + "'"
            else:
                return str(x)

        sql = "insert into " + db_schema + "." + db_table  \
            + "\n(" + ", ".join(list(body_json.keys())) + ")" \
            + "\nvalues(" + ", ".join(list(map(process_type, body_json.values()))) + ")"

        # 4. Insert data to the database
        with psycopg2.connect(host=db_host, 
                              port=db_port,
                              database=db_database, 
                              user=db_user, 
                              password=db_password) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
        conn.close()
        
        # 5. Return the result
        return "", 200


@app.route("/analytics/query", methods=["GET"])
def getAnalyticsData():
    "Get analytics data from database"

    if request.method == "GET":

        # 1. Get the parameters from URL
        parameters = {}
        parameters["groupBy"] = request.args.get("groupBy")
        parameters["metrics"] = request.args.get("metrics")
        parameters["granularity"] = request.args.get("granularity")
        parameters["startDate"] = request.args.get("startDate")
        parameters["endDate"] = request.args.get("endDate")
        parameters["filters"] = request.args.get("filters")

        # 2. Verify the specified parameters

        # 2.1. Check that all required parameters are specified
        for parameter in ["groupBy", "metrics", "granularity"]:
            if (parameter not in parameters.keys()):
                return "Error: " + parameter + " is required", 405
            elif parameters[parameter] is None:
                return "Error: " + parameter + " is required", 405

        # 2.2. Check the parameter values
        valid_parameters = {"groupBy": ["attribute1", "attribute2", "attribute3", 
                                        "attribute4", "attribute5", "attribute6"],
                            "metrics": ["metric1", "metric2"]}
        for parameter in ["groupBy", "metrics"]:
            specified_parameter_values = parameters[parameter].split(",")
            for i in range(len(specified_parameter_values)):
                if specified_parameter_values[i] not in valid_parameters[parameter]:
                    return "Error: " + specified_parameter_values[i] + " is invalid for the " + parameter + " parameter", 405
                
        if parameters["granularity"] not in ["hourly", "daily"]:
            return "Error: " + parameters["granularity"] + " is invalid for the granularity parameter", 405
            
        for parameter in ["startDate", "endDate"]:
            if parameters[parameter] is not None:
                try:
                    datetime.strptime(parameters[parameter], "%Y-%m-%dT%H:%M:%S")
                except:
                    return "Error: The format for " + parameter + " is incorrect", 405
                    
        if parameters["filters"] is not None:
            try:
                filters = json.loads(parameters["filters"])
            except:
                return "Error: invalid format for filters parameter", 405
            for parameter in filters.keys():
                if parameter not in ["attribute1", "attribute2", "attribute3", 
                                     "attribute4", "attribute5", "attribute6"]:
                    return "Error: entry " + parameter + " is incorrect for the filters parameter", 405
            prop_required_types = \
                {"attribute1": int, "attribute2": int, "attribute3": int, 
                 "attribute4": str, "attribute5": str, "attribute6": bool}
            for item in filters.items():
                if not isinstance(item[1], prop_required_types[item[0]]):
                    return "Error: " + item[0] + " entry in filters has an incorrect type", 405
                elif isinstance(item[1], str):
                    filters[item[0]] = "'" + filters[item[0]] + "'"

        # 3. If we reached this point, create SQL SELECT statement
        if parameters["granularity"] == "hourly":
            date_trunc_parameter = "hour"
        elif parameters["granularity"] == "daily":
            date_trunc_parameter = "day"

        sql = """with t as 
                (
                    select 
                        """ + parameters["groupBy"] + """,
                        date_trunc('""" + date_trunc_parameter + """', event_date) as date,
                        """ +  parameters["metrics"] + """
                    from """ + db_schema + "." + db_table
    
        if (parameters["filters"] is not None) or (parameters["startDate"] is not None) \
        or (parameters["endDate"] is not None):
            sql += """
                    where 1 = 1
                    """            
        if parameters["filters"] is not None:
            for item in filters.items():
                sql += "  and " + item[0] + " = " + str(item[1]) + """
                    """                
        if parameters["startDate"] is not None:
            sql += "  and event_date >= '" + parameters["startDate"] + """'
                    """            
        if parameters["endDate"] is not None:
            sql += "  and event_date <= '" + parameters["endDate"] + "'"
            
        sql += """
            )
            select 
                """ + parameters["groupBy"] + """,
                to_char(date, 'YYYY_MM_DD') || 'T' || to_char(date, 'HH:MI:SS') as date
                """
    
        metrics_list = parameters["metrics"].split(",")
        for i in range(len(metrics_list)):
            if metrics_list[i] == "metric1":
                sql += ", cast(sum(" + metrics_list[i] + ") as bigint) as " + metrics_list[i]
            else:
                sql += ", sum(" + metrics_list[i] + ") as " + metrics_list[i]
            
        sql += """
            from t
            group by """ + parameters["groupBy"] + """, date
            order by date, """ + parameters["groupBy"]

        # 4. Execute the query and get the result
        with psycopg2.connect(host=db_host, 
                              port=db_port,
                              database=db_database, 
                              user=db_user, 
                              password=db_password) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                row_headers = [x[0] for x in cur.description]
                results = cur.fetchall()
        conn.close()

        # 5. Return the result
        json_data = [dict(zip(row_headers, result)) for result in results]
        return json.dumps(json_data), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0")