class DailyReportDomainException(Exception):
    pass

class NotAssignedException(DailyReportDomainException):
    def __init__(self, message="L'employé n'est pas assigné à ce projet."):
        super().__init__(message)

class DuplicateReportException(DailyReportDomainException):
    def __init__(self, message="Un rapport hebdomadaire a déjà été soumis pour ce projet cette semaine."):
        super().__init__(message)
