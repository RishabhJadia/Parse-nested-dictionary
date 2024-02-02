        # Extract and store message header
        message_header = {
            'MsgId': md.MsgId.hex(),
            'CorrelId': md.CorrelId.hex(),
            'GroupId': md.GroupId.hex(),
            'MsgType': get_message_type(md.MsgType),
            'Expiry': md.Expiry,
            'Encoding': md.Encoding,
            'CodedCharSetId': md.CodedCharSetId,
            'Format': md.Format.strip(),
            'Priority': md.Priority,
            'Persistence': get_persistence(md.Persistence),
            'MsgSeqNumber': md.MsgSeqNumber,
            'Offset': md.Offset,
            'Feedback': md.Feedback,
            'AccountingToken': md.AccountingToken.hex(),
            'ApplIdentityData': md.ApplIdentityData.strip(),
            'PutApplType': md.PutApplType,
            'PutApplName': md.PutApplName.strip(),
            'PutDate': md.PutDate.strip(),
            'PutTime': md.PutTime.strip(),
            'ApplOriginData': md.ApplOriginData.strip(),
            'Content': message.decode()
        }
