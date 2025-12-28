package simple.tasks.controllers;

import edu.umd.cs.findbugs.annotations.SuppressFBWarnings;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;
import simple.tasks.dto.TaskResource;
import simple.tasks.dto.TasksDto;
import simple.tasks.models.Tasks;
import simple.tasks.services.*;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Objects;

@SuppressFBWarnings(value = "EI_EXPOSE_REP2", justification = "Spring services are injected once and treated as immutable dependencies")
@RestController
@Tag(name = "Tasks", description = "API de gestion des tâches")
public class TasksControllers {
    private final TasksCreateTask createTasksService;
    private final TasksGetTaskById tasksGetTaskByIdService;
    private final TasksGetAllTasks tasksGetAllTasks;
    private final UpdateTask updateTasksService;
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
    @Operation(summary = "Lister toutes les tâches", description = "Retourne la liste des tâches existantes avec des liens hypermedia")
    @ApiResponse(
        responseCode = "200",
        description = "Liste de tâches retournée",
        content = @Content(mediaType = "application/json", schema = @Schema(implementation = TaskResource.class))
    )
    public List<TaskResource> getAllTasks() {
        return tasksGetAllTasks.getAllTasks()
            .stream()
            .map(TaskResource::new)
            .toList();
    }

    @GetMapping("/tasks/{id}")
    @Operation(summary = "Récupérer une tâche par id")
    @ApiResponse(
        responseCode = "200",
        description = "Tâche trouvée",
        content = @Content(mediaType = "application/json", schema = @Schema(implementation = TaskResource.class))
    )
    @ApiResponse(responseCode = "404", description = "Tâche non trouvée")
    public TaskResource getTaskById(@PathVariable Long id) {
        Tasks task = tasksGetTaskByIdService.getTaskById(id);
        return new TaskResource(task);
    }

    @PostMapping("/tasks")
    @Operation(summary = "Créer une nouvelle tâche")
    @ApiResponse(
        responseCode = "201",
        description = "Tâche créée",
        content = @Content(mediaType = "application/json", schema = @Schema(implementation = TaskResource.class))
    )
    public TaskResource createTask(@RequestBody TasksDto task) {
        Tasks created = createTasksService.createTask(task);
        return new TaskResource(created);
    }

    @PutMapping("/tasks/{id}")
    @Operation(summary = "Mettre à jour une tâche existante")
    @ApiResponse(
        responseCode = "200",
        description = "Tâche mise à jour",
        content = @Content(mediaType = "application/json", schema = @Schema(implementation = TaskResource.class))
    )
    @ApiResponse(responseCode = "404", description = "Tâche non trouvée")
    public TaskResource updateTask(@PathVariable Long id, @RequestBody TasksDto task) {
        Tasks updated = updateTasksService.updateTask(id, task);
        return new TaskResource(updated);
    }

    @DeleteMapping("/tasks/{id}")
    @Operation(summary = "Supprimer une tâche")
    @ApiResponse(responseCode = "204", description = "Tâche supprimée")
    @ApiResponse(responseCode = "404", description = "Tâche non trouvée")
    public void deleteTask(@PathVariable Long id) {
        deleteTasksService.deleteTask(id);
    }
}
