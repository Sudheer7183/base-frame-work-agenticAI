

import pandas as pd
from langgraph.graph import StateGraph,START, END
# from typing_extensions import TypedDict
from typing import TypedDict, List, Dict, Optional
from langgraph.types import Send
import xml.etree.ElementTree as ET 
from datetime import datetime

class IngestionState(TypedDict):
    excel_records: List[dict]
    xml_records: List[dict]
    audit_xl_records:List[dict]
    variance: List[dict]


def calculate_payroll_periods(start_date, end_date, frequency):
    delta_days = (end_date - start_date).days

    if frequency == "1W":
        return delta_days / 7

    elif frequency == "1M":
        # Accurate month calculation
        months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

        # Adjust if end day is smaller than start day
        if end_date.day < start_date.day:
            months -= 1

        return months

    else:
        raise ValueError(f"Unsupported Payroll Frequency: {frequency}")

def parsexlxnode(state:IngestionState):
    filepath="/mnt/d/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/workmendata/Beach_Bazaar_of_Sarasota_Inc_2026_2_24.xlsx"
    df= pd.read_excel(filepath)
    records = []
    def safe_float(value):
        if pd.isna(value):
            return 0.0
        return float(value)
    for __, row in df.iterrows():
        records.append({
            "client_name": str(row.get("Client Name","")),
            "policy_number": str(row.get("Policy Number","")),
            "checkdate": str(row.get("CheckDate","")),
            "EENo": str(row.get("EE No","")),
            "Employee_name": str(row.get("Employee Name","")),
            "stateCode": str(row.get("St.","")),
            # "class_code": str(row.get("Class Code","")),
            "class_code": str(int(row.get("Class Code"))) if pd.notna(row.get("Class Code")) else "",

            "Wages": safe_float(row.get("Wages")),
            "over_time_pay": safe_float(row.get("OT")),
            "DT": safe_float(row.get("OT")),
            "Tips": safe_float(row.get("Tips")),
            "Net": safe_float(row.get("Net")),
            "Exposure": safe_float(row.get("Exposure")),
            "Net_rate": safe_float(row.get("Net Rate")),
            "Earned_premium": safe_float(row.get("Earned Prem.")),
            "census_rate": safe_float(row.get("Census Rate")),
            "census_premium": safe_float(row.get("Census Prem.")),

            "policyEffctivedate": str(row.get("Pol Eff. Date","")),
            "process_date": str(row.get("Process Date",""))
        })

    print("records values", [r["policy_number"] for r in records[:10]])

    return {"excel_records":records}




def parsexml(state: IngestionState):

    import xml.etree.ElementTree as ET
    from datetime import datetime

    filepathxml = "/mnt/d/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/workmendata/beach_bazar.xml"

    records_xml = []

    tree = ET.parse(filepathxml)
    root = tree.getroot()

    # ----------------------------
    # Policy Information
    # ----------------------------
    policyNode = root.find("Policy")

    transactionType = policyNode.findtext("TransactionType")
    NumberRetryDays = policyNode.findtext("NumberRetryDays")

    print("transaction type data", transactionType)

    policydataNode = policyNode.find("PolicyData")

    PolicyNumber = policydataNode.findtext("PolicyNumber")
    EffectiveDate = policydataNode.findtext("EffectiveDate")
    ExpirationDate = policydataNode.findtext("ExpirationDate")
    InsuredName = policydataNode.findtext("InsuredName")
    Premium = float(policydataNode.findtext("Premium"))

    # ----------------------------
    # Payroll Week Calculations
    # ----------------------------
    first_check_date = datetime.strptime("03/07/2025", "%m/%d/%Y")
    last_check_date = datetime.strptime("02/20/2026", "%m/%d/%Y")

    Number_of_Payroll_Reports_Submitted = 46
    PayrollFrequency = "1M"

    date1 = datetime.strptime(EffectiveDate, "%m/%d/%Y")
    date2 = datetime.strptime(ExpirationDate, "%m/%d/%Y")

    # expected_payroll_submissions = (date2 - date1).days / 7
    expected_payroll_submissions = calculate_payroll_periods(date1, date2, PayrollFrequency)
    # actual_payroll_submissions = (last_check_date - first_check_date).days / 7
    actual_payroll_submissions = calculate_payroll_periods(first_check_date, last_check_date, PayrollFrequency)

    print("number of weeks", expected_payroll_submissions, actual_payroll_submissions)

    # ----------------------------
    # States and Class Codes
    # ----------------------------
    StateNode = policyNode.find("States")

    for state_node in StateNode.findall("ComplexRateState"):

        State = state_node.findtext("State")

        rates_node = state_node.find("TimePeriod").find("Rates")

        for rate in rates_node.findall("Rate"):

            ClassCode = str(int(rate.findtext("ClassCode")))
            CompositeRate = float(rate.findtext("CompositeRate"))
            Exposure = float(rate.findtext("Exposure"))
            EstPremium = float(rate.findtext("EstPremium"))

            EstCCpremium = Exposure * CompositeRate

            records_xml.append({
                "PolicyNumber": PolicyNumber,
                "EffectiveDate": EffectiveDate,
                "ExpirationDate": ExpirationDate,
                "InsuredName": InsuredName,
                "premium": Premium,
                "StateCode": State,
                "classCode": ClassCode,
                "CompositeRate": CompositeRate,
                "Exposure": Exposure,
                "EstPremium": EstPremium,
                "EstCCpremium": EstCCpremium,
                "Number_of_Payroll_Reports_Submitted": Number_of_Payroll_Reports_Submitted,
                "expected_payroll_submissions": expected_payroll_submissions,
                "actual_payroll_submissions": actual_payroll_submissions
            })

    print("records of xml data", records_xml)

    return {"xml_records": records_xml}


def varianceNode(state: IngestionState):

    excel_records = state["excel_records"]
    xml_records = state["xml_records"]
    audit_records = state["audit_xl_records"][0]
    payroll_frequency = audit_records["a_payroll_frequency"]
    effective_date = xml_records[0]["EffectiveDate"]
    expiration_date = xml_records[0]["ExpirationDate"]

    date1 = datetime.strptime(effective_date, "%m/%d/%Y")
    date2 = datetime.strptime(expiration_date, "%m/%d/%Y")

    expected_payroll_submissions = calculate_payroll_periods(date1, date2, payroll_frequency)

    print("audit records from the variance node", audit_records["a_actual_payroll_submissions"])
    class_code_results = []

    # overall accumulators
    total_final_earned_exposure = 0
    total_final_earned_premium = 0
    total_est_exposure = 0
    total_est_ytd_premium = 0

    for xml_record in xml_records:

        exposure_value = []
        earned_premium = []

        for record in excel_records:

            if (
                record["policy_number"] == xml_record["PolicyNumber"].strip()
                and record["class_code"] == xml_record["classCode"].strip()
                and record["stateCode"] == xml_record["StateCode"].strip()
            ):
                exposure_value.append(record["Exposure"])
                earned_premium.append(record["Earned_premium"])

        final_earned_exposure = sum(exposure_value)
        final_earned_premium = sum(earned_premium)

        est_exposure = (
            float(xml_record["Exposure"])
            / expected_payroll_submissions
        ) * audit_records["number_of_payroll_submitted"]

        est_ytd_premium = (
            xml_record["EstCCpremium"]
            / expected_payroll_submissions
        ) * audit_records["number_of_payroll_submitted"]

        variance = final_earned_premium - est_ytd_premium

        variance_percentage = 0
        if est_ytd_premium != 0:
            variance_percentage = (variance / est_ytd_premium) * 100

        # store per class code results
        class_code_results.append({
            "PolicyNumber": xml_record["PolicyNumber"],
            "StateCode": xml_record["StateCode"],
            "ClassCode": xml_record["classCode"],
            "final_earned_exposure": final_earned_exposure,
            "final_earned_premium": final_earned_premium,
            "est_exposure": est_exposure,
            "est_ytd_premium": est_ytd_premium,
            "variance": variance,
            "variance_percentage": variance_percentage
        })

        # accumulate totals
        total_final_earned_exposure += final_earned_exposure
        total_final_earned_premium += final_earned_premium
        total_est_exposure += est_exposure
        total_est_ytd_premium += est_ytd_premium


    # overall variance calculation
    overall_variance = total_final_earned_premium - total_est_ytd_premium

    overall_variance_percentage = 0
    if total_est_ytd_premium != 0:
        overall_variance_percentage = (overall_variance / total_est_ytd_premium) * 100

    
    overall_results = {
        "final_earned_exposure": total_final_earned_exposure,
        "final_earned_premium": total_final_earned_premium,
        "est_exposure": total_est_exposure,
        "est_ytd_premium": total_est_ytd_premium,
        "variance": overall_variance,
        "variance_percentage": overall_variance_percentage
    }

    print("class code results",class_code_results),
    print("overall results",overall_results)
    return {
        "class_code_variance": class_code_results,
        "overall_variance": overall_results
    }


def auditxlxnode(state: IngestionState):
    filepath="/mnt/d/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/workmendata/Beach_Bazaar_of_Sarasota_Inc_auditReport_2026_2_24.xlsx"
    raw_df = pd.read_excel(filepath, header=None)

    header_row = None

    print("df audit data",raw_df)
    for i, row in raw_df.iterrows():
        if row.astype(str).str.contains("First Check Date Reported", case=False, na=False).any():
            header_row = i
            break

    if header_row is None:
        raise ValueError("Header row not found")
    
    df = pd.read_excel(filepath, header=header_row)

    audit_records = []
    for __,row in df.iterrows():
        audit_records.append({
            "last_checkdate":str(row.get("Last Check Date Reported","")),
            "first_checkdate":str(row.get("First Check Date Reported", "")),
            "number_of_payroll_submitted":str(row.get("Number of Payroll Reports Submitted","")),
            "PayrollFrequency":str(row.get("Payroll Frequency", " "))
        })

    print("audit recorords",audit_records)

    first_checkdate = audit_records[0]["first_checkdate"]
    last_checkdate = audit_records[0]["last_checkdate"]
    number_of_payroll_submitted= float(audit_records[0]["number_of_payroll_submitted"])
    payroll_frequency = str(audit_records[0]["PayrollFrequency"])
    c_first_checkdate= datetime.strptime(first_checkdate,"%m/%d/%Y")
    c_last_checkdate = datetime.strptime(last_checkdate,"%m/%d/%Y")

    # a_actual_payroll_submissions = (c_last_checkdate-c_first_checkdate).days /7
    a_actual_payroll_submissions = calculate_payroll_periods(
        c_first_checkdate,
        c_last_checkdate,
        payroll_frequency
    )

    print("a_actual_payroll_submissions",a_actual_payroll_submissions)

    final_audit_records = []

    final_audit_records.append({
        "a_actual_payroll_submissions":a_actual_payroll_submissions,
        "number_of_payroll_submitted":number_of_payroll_submitted,
        "a_payroll_frequency":payroll_frequency,
    })
    print("final audit reports",final_audit_records)

    return ({"audit_xl_records":final_audit_records})


def build_ingestion_graph(input_data):

    builder = StateGraph(IngestionState)

    # add nodes
    builder.add_node("excel_reader", parsexlxnode)
    builder.add_node("xml_reader", parsexml)
    builder.add_node("audit_reader",auditxlxnode)
    builder.add_node("variance_node",varianceNode)

    # edges from START
    builder.add_edge(START, "excel_reader")
    builder.add_edge(START,"audit_reader")
    builder.add_edge("excel_reader", "xml_reader")
    builder.add_edge("xml_reader", "variance_node")
    builder.add_edge("variance_node", END)
    builder.add_edge("audit_reader",END)

    graph = builder.compile()

    return graph