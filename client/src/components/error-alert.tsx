'use client'

import { useState } from 'react'
import { Dialog, DialogBackdrop, DialogPanel, DialogTitle } from '@headlessui/react'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

type ErrorAlertProps = {
    open: boolean
    setOpen: (value: boolean) => void
  }

export default function ErrorAlert({open, setOpen }: ErrorAlertProps) {
    return (
        <>
        { open ? (
            <div className='rounded-xl bg-red-300 px-5 py-5 flex'>
                <ExclamationTriangleIcon aria-hidden="true" className="size-6 mr-2 text-red-900" /> 
                <p className='text-red-900'>An error occured. Please try again later.</p>
            </div>
        ) : (<div></div>)
        }
        </>
    )
}