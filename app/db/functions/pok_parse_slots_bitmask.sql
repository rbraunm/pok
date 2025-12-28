CREATE FUNCTION `pok_parse_slots_bitmask`(p_slots INT)
RETURNS VARCHAR(255)
DETERMINISTIC
READS SQL DATA
BEGIN
  DECLARE v_idx INT DEFAULT 0;
  DECLARE v_result VARCHAR(255) DEFAULT '';
  DECLARE v_sn VARCHAR(32);
  DECLARE v_used_mask BIGINT UNSIGNED DEFAULT 0;
  DECLARE v_effective BIGINT UNSIGNED;

  IF p_slots IS NULL OR p_slots = 0 THEN
    RETURN '';
  END IF;

  -- Build mask of all *used* slots from eqemu_slots (omits 4,10,16 since they’re not in the table)
  SELECT SUM(1 << id) INTO v_used_mask FROM pok_eqemu_slots;

  SET v_effective = (p_slots & v_used_mask);

  -- If all used slots are set, return ALL
  IF v_effective = v_used_mask THEN
    RETURN 'All';
  END IF;

  -- Otherwise, list name for each set bit (space-separated)
  WHILE v_idx <= 22 DO
    IF (v_effective & (1 << v_idx)) <> 0 THEN
      SET v_sn = NULL;
      SELECT name INTO v_sn
      FROM pok_eqemu_slots
      WHERE id = v_idx
      LIMIT 1;

      IF v_sn IS NOT NULL THEN
        SET v_result = IF(v_result = '', v_sn, CONCAT(v_result, ' ', v_sn));
      END IF;
    END IF;

    SET v_idx = v_idx + 1;
  END WHILE;

  RETURN v_result;
END
