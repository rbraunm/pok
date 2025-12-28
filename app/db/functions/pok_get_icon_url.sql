CREATE FUNCTION pok_get_icon_url (
  icon_id         INT UNSIGNED,
  cols_per_page   INT UNSIGNED,
  rows_per_page   INT UNSIGNED,
  start_icon_id   INT UNSIGNED,
  scan_col_major  TINYINT UNSIGNED   -- 0=row-major, 1=column-major
)
RETURNS TEXT
DETERMINISTIC
SQL SECURITY INVOKER
BEGIN
  DECLARE page_size        BIGINT UNSIGNED;
  DECLARE idx              BIGINT SIGNED;
  DECLARE page_idx0        BIGINT UNSIGNED;
  DECLARE offset_in_page0  BIGINT UNSIGNED;
  DECLARE row_idx0         BIGINT UNSIGNED;
  DECLARE col_idx0         BIGINT UNSIGNED;

  IF cols_per_page = 0 OR rows_per_page = 0 OR icon_id < start_icon_id THEN
    RETURN NULL;
  END IF;

  SET page_size       = cols_per_page * rows_per_page;
  SET idx             = icon_id - start_icon_id;         -- 0-based from start
  SET page_idx0       = FLOOR(idx / page_size);          -- 0-based page
  SET offset_in_page0 = MOD(idx, page_size);             -- 0-based within page

  IF scan_col_major <> 0 THEN
    -- Column-major: top→bottom first, then left→right
    SET row_idx0 = MOD(offset_in_page0, rows_per_page);        -- 0..rows-1
    SET col_idx0 = FLOOR(offset_in_page0 / rows_per_page);     -- 0..cols-1
  ELSE
    -- Row-major: left→right first, then top→bottom
    SET row_idx0 = FLOOR(offset_in_page0 / cols_per_page);     -- 0..rows-1
    SET col_idx0 = MOD(offset_in_page0, cols_per_page);        -- 0..cols-1
  END IF;

  RETURN CONCAT(page_idx0 + 1, '.png?col=', col_idx0, '&row=', row_idx0);
END
