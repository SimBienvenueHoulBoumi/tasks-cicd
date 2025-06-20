package simple.tasks.controllers;

import lombok.AllArgsConstructor;

import simple.tasks.dto.TasksDto;
import simple.tasks.models.Tasks;
import simple.tasks.services.DeleteTask;
import simple.tasks.services.TasksCreateTask;
import simple.tasks.services.TasksGetAllTasks;
import simple.tasks.services.TasksGetTaskById;
import simple.tasks.services.UpdateTask;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

import lombok.AllArgsConstructor;

@AllArgsConstructor
@RestController
public class TasksControllers {
    private final TasksCreateTask createTasksService;
    private final TasksGetTaskById tasksGetTaskByIdService;
    private final TasksGetAllTasks tasksGetAllTasks;
    private final UpdateTask updateTasksService;
    private final DeleteTask deleteTasksService;

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
    public Tasks updateTask(@PathVariable Long id,@RequestBody TasksDto task) {
        return updateTasksService.updateTask(id, task);
    }

    @DeleteMapping("/tasks/{id}")
    public void deleteTask(@PathVariable Long id) {
        deleteTasksService.deleteTask(id);
    }
}
