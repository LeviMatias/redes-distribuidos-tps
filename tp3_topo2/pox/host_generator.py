def get_host(host_number):
    
    if host_number < 10:
        mac_host_number = '0'+str(host_number)
    else:
        mac_host_number = str(host_number)

    return 'h'+str(host_number), '10.0.0.'+str(host_number), '00:00:00:00:00:'+mac_host_number