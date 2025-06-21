package simple.tasks.services;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import simple.tasks.exceptions.ResourceNotFoundException;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

@Service
@AllArgsConstructor
public class TasksGetTaskById {
    private final TasksRepository tasksRepository;

    public Tasks getTaskById(Long id) {
        return tasksRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Task not found with id " + id));
        }
}
