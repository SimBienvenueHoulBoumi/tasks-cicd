package simple.tasks.services;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;

import org.springframework.stereotype.Service;

import simple.tasks.dto.TasksDto;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

@Service
@AllArgsConstructor
public class TasksCreateTask {
    private final TasksRepository tasksRepository;

    public Tasks createTask(TasksDto task) {
        Tasks newTask = new Tasks(task.getName());
        return tasksRepository.save(newTask);
    }
}
