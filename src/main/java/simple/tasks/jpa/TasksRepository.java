package simple.tasks.jpa;

import org.springframework.data.jpa.repository.JpaRepository;
import simple.tasks.models.Tasks;

public interface TasksRepository extends JpaRepository<Tasks, Long> {
}
