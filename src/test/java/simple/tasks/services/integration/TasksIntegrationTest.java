package simple.tasks.services.integration;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Tests d'intégration pour l'API Tasks.
 * <p>
 * Démarre tout le contexte Spring Boot (web, JPA, H2 in-memory) et
 * vérifie le comportement de bout en bout (HTTP <-> contrôleur <-> services <-> repository).
 */
@SpringBootTest
@AutoConfigureMockMvc
class TasksIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private TasksRepository tasksRepository;

    @BeforeEach
    void cleanDatabase() {
        tasksRepository.deleteAll();
    }

    @Test
    @DisplayName("GET /tasks retourne les tâches persistées (intégration complète)")
    void getAllTasks_returnsPersistedTasks() throws Exception {
        // Arrange : persiste une tâche en base H2 via le repository réel
        Tasks task = new Tasks("Faire les courses");
        task = tasksRepository.save(task);

        // Act + Assert : appel HTTP réel via MockMvc, stack complète
        mockMvc.perform(get("/tasks").accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$[0].id").value(task.getId()))
            .andExpect(jsonPath("$[0].name").value("Faire les courses"))
            .andExpect(jsonPath("$[0]._links.self").value("/tasks/" + task.getId()));
    }

    @Test
    @DisplayName("POST /tasks crée une tâche et la persiste en base (intégration complète)")
    void createTask_persistsTask() throws Exception {
        // Arrange
        long before = tasksRepository.count();

        String json = """
            { "name": "Nouvelle tâche intégration" }
            """;

        // Act : appel HTTP POST
        mockMvc.perform(post("/tasks")
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").isNumber())
            .andExpect(jsonPath("$.name").value("Nouvelle tâche intégration"));

        // Assert : la tâche est bien créée en base
        long after = tasksRepository.count();
        assertThat(after).isEqualTo(before + 1);
    }

    @Test
    @DisplayName("GET /tasks/{id} retourne une tâche existante (intégration complète)")
    void getTaskById_returnsSingleTask() throws Exception {
        // Arrange : persiste une tâche
        Tasks task = new Tasks("Lire un livre");
        task = tasksRepository.save(task);

        // Act + Assert
        mockMvc.perform(get("/tasks/{id}", task.getId())
                .accept(MediaType.APPLICATION_JSON))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(task.getId()))
            .andExpect(jsonPath("$.name").value("Lire un livre"))
            .andExpect(jsonPath("$._links.self").value("/tasks/" + task.getId()));
    }

    @Test
    @DisplayName("PUT /tasks/{id} met à jour une tâche existante (intégration complète)")
    void updateTask_updatesPersistedTask() throws Exception {
        // Arrange : persiste une tâche
        Tasks task = new Tasks("Ancien nom");
        task = tasksRepository.save(task);

        String json = """
            { "name": "Nom mis à jour" }
            """;

        // Act
        mockMvc.perform(put("/tasks/{id}", task.getId())
                .contentType(MediaType.APPLICATION_JSON)
                .content(json))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.id").value(task.getId()))
            .andExpect(jsonPath("$.name").value("Nom mis à jour"));

        // Assert : vérifie en base
        Tasks reloaded = tasksRepository.findById(task.getId()).orElseThrow();
        assertThat(reloaded.getName()).isEqualTo("Nom mis à jour");
    }

    @Test
    @DisplayName("DELETE /tasks/{id} supprime une tâche existante (intégration complète)")
    void deleteTask_removesPersistedTask() throws Exception {
        // Arrange : persiste une tâche
        Tasks task = new Tasks("À supprimer");
        task = tasksRepository.save(task);

        long before = tasksRepository.count();

        // Act
        mockMvc.perform(delete("/tasks/{id}", task.getId()))
            .andExpect(status().isOk());

        // Assert
        long after = tasksRepository.count();
        assertThat(after).isEqualTo(before - 1);
        assertThat(tasksRepository.findById(task.getId())).isEmpty();
    }
}


