package simple.tasks.controllers;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import simple.tasks.dto.TaskResource;
import simple.tasks.dto.TasksDto;
import simple.tasks.models.Tasks;
import simple.tasks.services.*;

import java.util.List;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Tests de contrôleur pour {@link TasksControllers}.
 * <p>
 * Ces tests couvrent les principaux endpoints REST pour améliorer la
 * couverture de code et valider le mapping JSON de base.
 */
@ExtendWith(MockitoExtension.class)
class TasksControllersTest {

    private MockMvc mockMvc;

    @InjectMocks
    private TasksControllers controller;

    @Mock
    private TasksCreateTask createTasksService;

    @Mock
    private TasksGetTaskById tasksGetTaskByIdService;

    @Mock
    private TasksGetAllTasks tasksGetAllTasks;

    @Mock
    private UpdateTask updateTasksService;

    @Mock
    private DeleteTask deleteTasksService;

    @BeforeEach
    void setUp() {
        mockMvc = MockMvcBuilders.standaloneSetup(controller).build();
    }

    @Test
    @DisplayName("GET /tasks doit retourner la liste des tâches avec un statut 200")
    void getAllTasks_returnsTaskList() throws Exception {
        Tasks task = new Tasks("Faire les courses");
        task.setId(1L);
        Mockito.when(tasksGetAllTasks.getAllTasks()).thenReturn(List.of(task));

        mockMvc.perform(get("/tasks").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].id").value(1L))
            .andExpect(jsonPath("$[0].name").value("Faire les courses"))
            .andExpect(jsonPath("$[0]._links.self").value("/tasks/1"));
    }

    @Test
    @DisplayName("GET /tasks/{id} doit retourner une tâche existante")
    void getTaskById_returnsSingleTask() throws Exception {
        Tasks task = new Tasks("Lire un livre");
        task.setId(2L);
        Mockito.when(tasksGetTaskByIdService.getTaskById(2L)).thenReturn(task);

        mockMvc.perform(get("/tasks/{id}", 2L).accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(2L))
            .andExpect(jsonPath("$.name").value("Lire un livre"))
            .andExpect(jsonPath("$._links.self").value("/tasks/2"));
    }

    @Test
    @DisplayName("POST /tasks doit créer une tâche et retourner 201")
    void createTask_createsTask() throws Exception {
        TasksDto payload = new TasksDto("Nouvelle tâche");
        Tasks created = new Tasks(payload.name());
        created.setId(3L);

        Mockito.when(createTasksService.createTask(Mockito.any(TasksDto.class)))
            .thenReturn(created);

        String json = """
            { "name": "Nouvelle tâche" }
            """;

        mockMvc.perform(post("/tasks")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(3L))
            .andExpect(jsonPath("$.name").value("Nouvelle tâche"));
    }

    @Test
    @DisplayName("PUT /tasks/{id} doit mettre à jour une tâche existante")
    void updateTask_updatesExistingTask() throws Exception {
        TasksDto payload = new TasksDto("Tâche mise à jour");
        Tasks updated = new Tasks(payload.name());
        updated.setId(4L);

        Mockito.when(updateTasksService.updateTask(Mockito.eq(4L), Mockito.any(TasksDto.class)))
            .thenReturn(updated);

        String json = """
            { "name": "Tâche mise à jour" }
            """;

        mockMvc.perform(put("/tasks/{id}", 4L)
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(4L))
            .andExpect(jsonPath("$.name").value("Tâche mise à jour"));
    }

    @Test
    @DisplayName("DELETE /tasks/{id} doit supprimer une tâche et retourner 204")
    void deleteTask_deletesTask() throws Exception {
        mockMvc.perform(delete("/tasks/{id}", 5L))
            .andExpect(status().isOk());

        Mockito.verify(deleteTasksService).deleteTask(5L);
    }
}


