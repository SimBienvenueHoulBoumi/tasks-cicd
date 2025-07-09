package simple.tasks.services;

import java.util.List;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;


import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

import java.util.Collections;

@Service
@AllArgsConstructor
public class TasksGetAllTasks {
    private final TasksRepository tasksRepository;

    public List<Tasks> getAllTasks() {
        return Collections.unmodifiableList(
            List.copyOf(tasksRepository.findAll())
        );
    }
}
