def get_response(**kwargs):
	try:
		response = {"haserror": False, "message": []}
		hcon, queue_name = kwargs['hcon'], kwargs['payload']['queue']
		queue = pymqi.Queue(hcon, queue_name, open_options)
		gmo = pymi.GMO()
		gmo.Version = pymqi.CMQC.MQMD_VERSION_2
		gmo.Options = pymqi.CMQC.MQGMO_WAIT | pymqi.CMQC.MQGMO_BROWSE_NEXT
		gmo.MatchOptions = pymqi.CMQC.MQMO_MATCH_MSG_ID | pymqi.CMQC.MQMO_CORREL_ID
		gmo.WaitInterval = 5000
		message_count = 0
		user_limit = kwargs['payload']['limit']
		if user_limit > 100:
			raise Badrequest("Limit cannot reached 100")
		msgid = kwargs['payload']['msgid']
		correlid = kwargs['payload']['correlid']
		while message_count < user_limit or msgid or correlid or (not user_limit and not msgid) or (not user_limit and not correlid) or (not user_limit and not correlid and not msgid):
		try:
			md = pymqi.MD()
    		md.Version = pymqi.CMQC.MQMD_VERSION_2
    		md.Format = pymqi.CMQC.MQFMT_STRING
    		if not (isinstance(msgid, bytes)) or not (isinstance(correlid, bytes)):
    			msgid = bytes.fromhex(msgid)
    			correlid = bytes.fromhex(correlid)

    		if user_limit:
    			if message_count == user_limit:
    				break
	    		message = queue.get(None, md, gmo)
	    		response['message'].append(message)
	    	elif msgid and correlid:
	    		msg.MsgId = msgid 
	    		msg.CorrelId = correlid
	    		message = queue.get(None, md, gmo)
	    		response['message'].append(message)
	    		break
	    	elif msgid:
	    		msg.MsgId = msgid 
	    		message = queue.get(None, md, gmo)
	    		response['message'].append(message)
	    		break
	    	elif msgid:
	    		msg.CorrelId = correlid
	    		message = queue.get(None, md, gmo)
	    		response['message'].append(message)
	    		break
	    	else:
	    		message = queue.get(None, md, gmo)
	    		response['message'].append(message)
	    		break
            except pymqi.MQMIError as e:
                if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
                    # No messages, that's OK, we can ignore it.
                    print("dump message")
                    break
                else:
                    raise
	except Exception as err:
		raise BadRequest(str(err))
	return response
------------------------------------------------------------------------------------------------------------------------------------------------
#Refactor 1:
def convert_to_bytes(value):
    if not isinstance(value, bytes):
        return bytes.fromhex(value)
    return value

class QueueHandler:

	def open_queue(self, hcon, queue_name, open_options):
		return pymqi.Queue(hcon, queue_name, open_options)
 
 
 class MessageProcessor:
    @staticmethod
    def process_message(queue, md, gmo):
        message = queue.get_message(md, gmo)
        return message

class MdStructure:
    def create_md(self):
		"""Creates an MD (Message Descriptor) structure with specified message ID and correlation ID."""
		md = pymqi.MD()
		md.Version = pymqi.CMQC.MQMD_VERSION_2
  		md.Format = pymqi.CMQC.MQFMT_STRING
		return md

class ResponseHandler:
    @staticmethod
    def add_message(response, message):
        response['message'].append(message)


def get_response(**kwargs):
	try:
		response = {"haserror": False, "message": []}
		hcon, queue_name = kwargs['hcon'], kwargs['payload']['queue']
		queue = QueueHandler.open_queue(hcon, queue_name, pymqi.CMQC.MQOO_BROWSE) 
		
		# Create a Get Message Options (GMO) object and Set options for the GMO
  		gmo = pymi.GMO()
		gmo.Version = pymqi.CMQC.MQMD_VERSION_2
		gmo.Options = pymqi.CMQC.MQGMO_WAIT | pymqi.CMQC.MQGMO_BROWSE_NEXT
		gmo.MatchOptions = pymqi.CMQC.MQMO_MATCH_MSG_ID | pymqi.CMQC.MQMO_CORREL_ID
		gmo.WaitInterval = 5000
		
  		user_limit = kwargs['payload']['limit']
		if user_limit > 100:
			raise Badrequest("Limit cannot reached 100")

		msgid, correlid = convert_to_bytes(kwargs['payload']['msgid']), convert_to_bytes(kwargs['payload']['correlid'])
  
		process_messages(queue=queue, gmo=gmo, user_limit=user_limit, msgid=msgid, correlid=correlid, response=response)

	except Exception as err:
		raise BadRequest(str(err))
	return response


def process_messages(queue, gmo, user_limit, msgid, correlid, response):
    message_count = 0
	while message_count < user_limit or msgid or correlid or (not user_limit and not msgid) or (not user_limit and not correlid) or (not user_limit and not correlid and not msgid):
		try:
			# md = pymqi.MD()
			# md.Version = pymqi.CMQC.MQMD_VERSION_2
			# md.Format = pymqi.CMQC.MQFMT_STRING
			md = MdStructure.create_md()
			if user_limit:
				if message_count == user_limit:
					break
				message = MessageProcessor.process_message(queue=queue, md=md, gmo=gmo)
				# message = queue.get(None, md, gmo)
				ResponseHandler.add_message(response, message)

			elif msgid and correlid:
				msg.MsgId = msgid 
				msg.CorrelId = correlid
    			message = MessageProcessor.process_message(queue=queue, md=md, gmo=gmo)
				ResponseHandler.add_message(response, message)
				# message = queue.get(None, md, gmo)
				# response['message'].append(message)
				break
			elif msgid:
				msg.MsgId = msgid 
				message = MessageProcessor.process_message(queue=queue, md=md, gmo=gmo)
				ResponseHandler.add_message(response, message)
				# message = queue.get(None, md, gmo)
				# response['message'].append(message)
				break
			elif msgid:
				msg.CorrelId = correlid
				message = MessageProcessor.process_message(queue=queue, md=md, gmo=gmo)
				ResponseHandler.add_message(response, message)
				# message = queue.get(None, md, gmo)
				# response['message'].append(message)
				break
			else:
				message = MessageProcessor.process_message(queue=queue, md=md, gmo=gmo)
				ResponseHandler.add_message(response, message)
				# message = queue_name.get(None, md, gmo)
				# response['message'].append(message)
				break
		except pymqi.MQMIError as e:
			if e.comp == pymqi.CMQC.MQCC_FAILED and e.reason == pymqi.CMQC.MQRC_NO_MSG_AVAILABLE:
				# No messages, that's OK, we can ignore it.
				print("dump message")
				break
			else:
				raise
