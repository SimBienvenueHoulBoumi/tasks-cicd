package simple.tasks.services;

import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import simple.tasks.dto.TasksDto;
import simple.tasks.exceptions.ResourceNotFoundException;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

@Service
@AllArgsConstructor
public class UpdateTask {
    private final TasksRepository tasksRepository;

    public Tasks updateTask(Long id, TasksDto task) {
        Tasks existingTask = tasksRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Task not found with id " + id));
        
        existingTask.setName(task.getName());
        return tasksRepository.save(existingTask);
    }
}
