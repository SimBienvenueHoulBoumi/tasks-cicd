package simple.tasks.models;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;

import lombok.NoArgsConstructor;
import lombok.Data;
import lombok.Data;

@Entity
@Data
@NoArgsConstructor
public class Tasks {
  private @Id
  @GeneratedValue Long id;
  private String name;

  public Tasks(String name) {
    this.name = name;
  }
}
