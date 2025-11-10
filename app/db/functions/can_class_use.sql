CREATE FUNCTION `can_class_use`(p_classes_mask INT, p_class_id INT)
RETURNS TINYINT(1)
DETERMINISTIC
NO SQL
BEGIN
  IF p_classes_mask IS NULL OR p_class_id IS NULL OR p_class_id <= 0 THEN
    RETURN 0;
  END IF;
  RETURN (p_classes_mask & (1 << (p_class_id - 1))) <> 0;
END
