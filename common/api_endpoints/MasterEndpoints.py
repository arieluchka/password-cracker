



class MasterEndpoints:
    class GET:
        MINIONS_STATUS = "/get-minions-status"
        STATUS = "/status/{hash_value}/{start_range}/{end_range}"
        HASH_REPORTS = "/get-hash-reports"

    class POST:
        MINION = "/add-minion"
        NEW_HASHES = "/add-new-hashes"
        CRACK_RESULT = "/crack-result"