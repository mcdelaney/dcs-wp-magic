CREATE OR REPLACE VIEW `dcs-analytics-257714`.tacview.comb AS (
  SELECT *, ST_GEOGPOINT(long, lat) as geo_pt
  FROM `dcs-analytics-257714`.tacview.events
  INNER JOIN (SELECT DISTINCT session_id, title, datasource
              FROM `dcs-analytics-257714`.tacview.sessions) sessions
  USING (session_id)
  INNER JOIN (SELECT DISTINCT id as object, session_id, name,
                color, country, grp, pilot, type, first_seen,
                coalition, parent
             FROM `dcs-analytics-257714`.tacview.objects)
  USING (object, session_id)
)
