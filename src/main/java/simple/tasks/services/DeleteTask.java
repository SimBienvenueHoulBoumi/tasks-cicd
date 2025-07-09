package simple.tasks.services;

import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import simple.tasks.exceptions.ResourceNotFoundException;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

@Service
@AllArgsConstructor
public final class DeleteTask { // Rend la classe immuable

    private final TasksRepository tasksRepository;

    public void deleteTask(final Long id) {
        final Tasks existingTask = tasksRepository.findById(id)
            .orElseThrow(() -> new ResourceNotFoundException("Task not found with id " + id));
        
        tasksRepository.delete(existingTask);
    }
}
