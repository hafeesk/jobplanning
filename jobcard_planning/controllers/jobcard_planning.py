import datetime

import frappe, json
from frappe import _
from frappe.utils import get_user_date_format
from frappe.utils.dateutils import dateformats



@frappe.whitelist()
def get_jobcard_planning_details(start, end, filters=None):

    events = []

    event_color = {
        "Open": "#2acced",
        "Working": "#ed982a",
        "Completed": "#cc5908",
    }

    from frappe.desk.reportview import get_filters_cond

    conditions = get_filters_cond("Task", filters, [])

    job_cards = frappe.db.sql(
        """  SELECT name,subject,
            status, 
            custom_expected_start_date_time,
            custom_expected_end_date_time,
            custom_team_lead,
            custom_qty,
            custom_site_status,
            custom_material_status,
            custom_project_name,
            custom_unit,
            custom_period,
            custom_total_hours,
            custom_team_strength
        FROM `tabTask` 
        WHERE
            status<>'Cancelled'
             {0}
            group by name""".format(
            conditions
        ),
        as_dict=1,debug=1
    )

    # Attemp to make it with query Builder, but there is no
    # to convert form filters to .where()

    # from frappe.query_builder.functions import Min, Max
    # JobCard = frappe.qb.DocType("Job Card")
    # JobCardTimeLog = frappe.qb.DocType("Job Card Time Log")
    # job_cards_query = (
    #     frappe.qb.from_(JobCard)
    #     .inner_join(JobCardTimeLog)
    #     .on(JobCard.name == JobCardTimeLog.parent)
    #     .groupby(JobCard.name)
    #     .having(Min(JobCardTimeLog.from_time) >= start)
    #     .having(Max(JobCardTimeLog.from_time) <= end)
    #     .select(
    #         JobCard.name,
    #         JobCard.work_order,
    #         JobCard.status,
    #         JobCard.remarks,
    #         JobCard.planned_start_date,
    #         JobCard.planned_end_date,
    #         Min(JobCardTimeLog.from_time).as_('initial_start_date'),
    #     )
    # )
    #job_cards = job_cards_query.run(as_dict=1)

    for d in job_cards:
        subject_data = []
        
        for field in ["custom_project_name", "subject", "custom_qty","custom_unit","custom_period","custom_total_hours",
                      "custom_team_lead", "custom_site_status", "custom_expected_start_date_time",
                      "custom_expected_end_date_time",'custom_material_status','custom_team_strength']:
            if not d.get(field):
                continue

            if field == 'custom_expected_start_date_time' or field == 'custom_expected_end_date_time':
                data_txt = d.get(field).strftime(dateformats[get_user_date_format()])
            elif field == 'custom_qty':
                data_txt = _("Qty")+':'+str(d.get(field))
            elif field == 'custom_team_lead':
                data_txt = _("Team Lead")+':'+frappe.db.get_value("Employee",d.get(field),'employee_name')
            elif field == 'custom_unit':
                data_txt = _("Unit")+':'+d.get(field)
            elif field == 'custom_period':
                data_txt = _("Period")+':'+str(d.get(field))
            elif field == 'custom_total_hours':
                data_txt = _("Total Hours")+':'+str(d.get(field))
            elif field == 'custom_project_name':
                data_txt = _("Project")+':'+d.get(field)
            elif field == 'custom_site_status':
                data_txt = _("Site Status")+':'+d.get(field)
            elif field == 'custom_material_status':
                data_txt = _("Material Status")+':'+d.get(field)
            elif field == 'custom_team_strength':
                data_txt = _("Team Strength")+':'+str(d.get(field))

            else:
                data_txt = d.get(field)

                
            subject_data.append(data_txt)
       
        emp_list='Employees:'
        empl = frappe.get_doc("Task",d.name)
        for emp in empl.custom_timesheet_employees:
            emp_list = emp_list + ',' + frappe.db.get_value("Employee",emp.employee,'employee_name')

        subject_data.append(emp_list)

        color = event_color.get(d.status)
        start_date = d.custom_expected_start_date_time
        end_date = d.custom_expected_end_date_time

        job_card_data = {
            "custom_expected_start_date_time": start_date,
            "custom_expected_end_date_time": end_date,
            "name": d.name,
            "subject": "\n".join(subject_data),
            "color": color,
            "allDay":0,
        }

        events.append(job_card_data)

    return events

@frappe.whitelist()
def update_jobcard_planned_date(args, field_map):
    """Updates Event (called via calendar) based on passed `field_map`"""
    args = frappe._dict(json.loads(args))
    field_map = frappe._dict(json.loads(field_map))
    w = frappe.get_doc(args.doctype, args.name)
    w.db_set(field_map.start, args[field_map.start])
    w.db_set(field_map.end, args.get(field_map.end))
