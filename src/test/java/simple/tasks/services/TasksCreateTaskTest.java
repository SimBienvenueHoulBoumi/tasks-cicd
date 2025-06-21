package simple.tasks.services;

import simple.tasks.dto.TasksDto;
import simple.tasks.models.Tasks;
import simple.tasks.jpa.TasksRepository;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.*;

class TasksCreateTaskTest {

    @Test
    void testCreateTask() {
        // Arrange
        TasksRepository mockRepo = mock(TasksRepository.class);
        TasksCreateTask service = new TasksCreateTask(mockRepo);

        TasksDto dto = new TasksDto("Nouvelle tâche");
        Tasks savedTask = new Tasks("Nouvelle tâche");

        when(mockRepo.save(any(Tasks.class))).thenReturn(savedTask);

        // Act
        Tasks result = service.createTask(dto);

        // Assert
        assertEquals("Nouvelle tâche", result.getName());
        verify(mockRepo, times(1)).save(any(Tasks.class));
    }
}
