CREATE OR REPLACE VIEW `dcs-analytics-257714`.tacview.comb AS (
  SELECT * FROM `dcs-analytics-257714`.tacview.events
  INNER JOIN (SELECT title, datasource, session_id
              FROM `dcs-analytics-257714`.tacview.sessions) sessions
  USING (session_id)
  INNER JOIN (SELECT id as object, session_id, name,
                color, country, grp, pilot, type, coalition, parent
             FROM `dcs-analytics-257714`.tacview.objects)
  USING (object, session_id)
)
