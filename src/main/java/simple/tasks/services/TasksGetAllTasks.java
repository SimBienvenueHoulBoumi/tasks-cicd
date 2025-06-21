package simple.tasks.services;
import java.util.List;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;


import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

@Service
@AllArgsConstructor
public class TasksGetAllTasks {
    private final TasksRepository tasksRepository;

    public List<Tasks> getAllTasks() {
        return tasksRepository.findAll();
    }

}
