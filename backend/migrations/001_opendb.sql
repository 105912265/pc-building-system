-- Project Phase 5: BuildCores OpenDB integration
-- RUN ON A BACKUP/COPY FIRST. Execute once in MySQL Workbench.
-- Preserve all existing component IDs, prices, build and review relationships.
USE pc_building_system;

-- OpenDB does NOT contain reliable prices; NULL means price unknown,
-- not free. Existing prices remain unchanged.
ALTER TABLE component
  MODIFY COLUMN price DECIMAL(10,2) NULL;

-- Each online UUID maps to one local component; rerunning the importer
-- updates linked records rather than creating duplicates.
CREATE TABLE IF NOT EXISTS component_source (
    source_name VARCHAR(32) NOT NULL,
    source_record_id CHAR(36) NOT NULL,
    component_id INT NOT NULL,
    last_imported_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
      ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (source_name, source_record_id),
    INDEX idx_component_source_component (component_id),
    CONSTRAINT fk_component_source_component FOREIGN KEY (component_id)
      REFERENCES component (component_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
