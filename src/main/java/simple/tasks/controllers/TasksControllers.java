package simple.tasks.controllers;

import lombok.Generated;
import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import org.springframework.web.bind.annotation.*;
import simple.tasks.dto.TasksDto;
import simple.tasks.models.Tasks;
import simple.tasks.services.*;

import java.util.List;
import java.util.Objects;

@RestController
public class TasksControllers {
    private final TasksCreateTask createTasksService;
    private final TasksGetTaskById tasksGetTaskByIdService;
    private final TasksGetAllTasks tasksGetAllTasks;
    private final UpdateTask updateTasksService;

    @SuppressFBWarnings(value = "EI_EXPOSE_REP2", justification = "Bean Spring injecté de manière sûre")
    private final DeleteTask deleteTasksService;

    public TasksControllers(
        TasksCreateTask createTasksService,
        TasksGetTaskById tasksGetTaskByIdService,
        TasksGetAllTasks tasksGetAllTasks,
        UpdateTask updateTasksService,
        DeleteTask deleteTasksService
    ) {
        this.createTasksService = Objects.requireNonNull(createTasksService);
        this.tasksGetTaskByIdService = Objects.requireNonNull(tasksGetTaskByIdService);
        this.tasksGetAllTasks = Objects.requireNonNull(tasksGetAllTasks);
        this.updateTasksService = Objects.requireNonNull(updateTasksService);
        this.deleteTasksService = Objects.requireNonNull(deleteTasksService);
    }

    @GetMapping("/tasks")
    public List<Tasks> getAllTasks() {
        return tasksGetAllTasks.getAllTasks();
    }

    @GetMapping("/tasks/{id}")
    public Tasks getTaskById(@PathVariable Long id) {
        return tasksGetTaskByIdService.getTaskById(id);
    }

    @PostMapping("/tasks")
    public Tasks createTask(@RequestBody TasksDto task) {
        return createTasksService.createTask(task);
    }

    @PutMapping("/tasks/{id}")
    public Tasks updateTask(@PathVariable Long id, @RequestBody TasksDto task) {
        return updateTasksService.updateTask(id, task);
    }

    @DeleteMapping("/tasks/{id}")
    public void deleteTask(@PathVariable Long id) {
        deleteTasksService.deleteTask(id);
    }
}
