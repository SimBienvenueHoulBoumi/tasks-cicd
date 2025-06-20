package simple.tasks.services;

import simple.tasks.jpa.TasksRepository;
import simple.tasks.models.Tasks;
import simple.tasks.exceptions.ResourceNotFoundException;

import org.junit.jupiter.api.Test;

import java.util.Optional;

import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.*;

class DeleteTaskTest {

    private final TasksRepository tasksRepository = mock(TasksRepository.class);
    private final DeleteTask service = new DeleteTask(tasksRepository);

    @Test
    void shouldDeleteTaskIfExists() {
        // Arrange
        Tasks task = new Tasks("To Delete");
        when(tasksRepository.findById(1L)).thenReturn(Optional.of(task));

        // Act
        service.deleteTask(1L);

        // Assert
        verify(tasksRepository).delete(task);
    }

    @Test
    void shouldThrowIfTaskNotFound() {
        // Arrange
        when(tasksRepository.findById(2L)).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(ResourceNotFoundException.class, () -> service.deleteTask(2L));
    }
}
