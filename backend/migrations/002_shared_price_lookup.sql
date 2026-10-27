-- Phase 5: authentication and daily AI-search usage.
-- Existing component/user tables and their data are NOT altered.
-- Take a Workbench full-data backup before running.
USE pc_building_system;

CREATE TABLE IF NOT EXISTS price_account (
  user_id INT NOT NULL PRIMARY KEY,
  password_hash VARCHAR(255) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user',
  account_tier ENUM('free','premium') NOT NULL DEFAULT 'free',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_price_account_user FOREIGN KEY (user_id) REFERENCES `user`(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ai_price_usage (
  user_id INT NOT NULL,
  usage_date DATE NOT NULL,
  used_count INT NOT NULL DEFAULT 0,
  PRIMARY KEY(user_id,usage_date),
  CONSTRAINT fk_price_usage_user FOREIGN KEY (user_id) REFERENCES `user`(user_id),
  CONSTRAINT chk_price_usage_nonnegative CHECK(used_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Verification:
SHOW TABLES LIKE 'price_account';
SHOW TABLES LIKE 'ai_price_usage';
-- Not creating price columns: latest price metadata goes into
-- component.specifications JSON -> $.price_metadata.
